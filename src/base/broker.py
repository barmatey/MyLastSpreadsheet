from typing import Iterable, Callable, Type
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ForeignKey, Column, String, Table, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.base.repo.postgres import Base
from src.helpers.decorators import singleton


class IBrokerService:
    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        raise NotImplemented

    async def unsubscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        raise NotImplemented

    async def get_subs(self, pub: BaseModel) -> set[BaseModel]:
        raise NotImplemented

    async def get_pubs(self, sub: BaseModel) -> set[BaseModel]:
        raise NotImplemented


class Entity(BaseModel):
    id: UUID
    key: str


association_table = Table(
    "pubsub_association_table",
    Base.metadata,
    Column("pub_id", ForeignKey("publisher.id"), primary_key=True),
    Column("sub_id", ForeignKey("subscriber.id"), primary_key=True),
)


class PublisherModel(Base):
    __tablename__ = "publisher"
    key: Mapped[str] = mapped_column(String(256))
    subs: Mapped[set['SubscriberModel']] = relationship(
        secondary=association_table, back_populates="pubs"
    )


class SubscriberModel(Base):
    __tablename__ = "subscriber"
    key: Mapped[str] = mapped_column(String(256))
    pubs: Mapped[set[PublisherModel]] = relationship(
        secondary=association_table, back_populates="subs"
    )


class BrokerRepoPostgres:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel) -> None:
        # Get already exist pubs
        pub_ids = set(x.id for x in pubs)
        pub_models = []
        exist_pub_models_ids = set()
        for x in await self._session.scalars(select(PublisherModel).where(PublisherModel.id.in_(pub_ids))):
            pub_models.append(x)
            exist_pub_models_ids.add(x.id)

        # Create new pubs if {pub_models gotten from db} < {pubs}
        to_create = []
        for pub in pubs:
            if pub.id not in exist_pub_models_ids:
                model = PublisherModel(id=pub.id, key=str(type(pub)), )
                to_create.append(model)
                pub_models.append(model)

        # Get subscriber if exists one or create if not
        sub_model = await self._session.scalar(select(SubscriberModel).where(SubscriberModel.id == sub.id))
        if sub_model is None:
            sub_model = SubscriberModel(id=sub.id, key=str(type(sub)))
            to_create.append(sub_model)
        sub_model.pubs = sub_model.pubs.union(pub_models)

        self._session.add_all(to_create)

    async def get_subs(self, pub: BaseModel) -> list[dict]:
        stmt = select(PublisherModel).where(PublisherModel.id == pub.id)
        model = await self._session.scalar(stmt)
        result = [{"id": x.id, "key": x.key} for x in model.subs]
        return result


class BrokerPostgres:

    def __init__(self, repo: BrokerRepoPostgres):
        self._repo = repo
        self._getter = {}

    def register(self, class_: Type, getter: Callable):
        key = str(class_)
        self._getter[key] = getter

    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        await self._repo.subscribe(pubs, sub)

    async def get_subs(self, pub: BaseModel) -> list[BaseModel]:
        subs = await self._repo.get_subs(pub)
        temp = {}
        for s in subs:
            if temp.get(s["key"]) is None:
                temp[s["key"]] = set()
            temp[s["key"]].add(s["id"])

        result: list[BaseModel] = []
        for key, ids in temp.items():
            getter = self._getter[key]
            entities: Iterable[BaseModel] = await getter(ids)
            result.extend(entities)

        return result


@singleton
class BrokerService(IBrokerService):
    def __init__(self):
        self._data: dict[BaseModel, set[BaseModel]] = {}

    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        for pub in pubs:
            if self._data.get(pub) is None:
                self._data[pub] = set()
            self._data[pub].add(sub)

    async def unsubscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        raise NotImplemented

    async def get_subs(self, pub: BaseModel) -> set[BaseModel]:
        if self._data.get(pub) is None:
            return set()
        return self._data[pub]

    async def get_pubs(self, sub: BaseModel) -> set[BaseModel]:
        result = set(key for key, value in self._data.items() if sub in value)
        return result
