from typing import Iterable, Callable, Type
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ForeignKey, Column, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapper, mapped_column, Mapped, relationship

from src.base.repo.postgres import Base
from src.helpers.decorators import singleton
from src.report.domain import Table


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
    key: Mapped[str] = mapped_column(String(32))
    children: Mapped[list['SubscriberModel']] = relationship(
        secondary=association_table, back_populates="pubs"
    )


class SubscriberModel(Base):
    __tablename__ = "subscriber"
    key: Mapped[str] = mapped_column(String(32))
    parents: Mapped[list[PublisherModel]] = relationship(
        secondary=association_table, back_populates="subs"
    )


class BrokerRepo:
    def __init__(self, session: AsyncSession):
        self._session = session




class BrokerPostgres:

    def __init__(self, repo):
        self._repo = repo
        self._getter = {}

    def register(self, class_: Type, getter: Callable):
        key = str(class_)
        self._getter[key] = getter

    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        key = str(type(sub))
        entity = Entity(id=sub.id, key=key)
        await self._repo.add(entity)

    async def get_subs(self, pub: BaseModel) -> set[BaseModel]:
        subs: list[Entity] = await self._repo.get_subs(pub.id)
        temp = {}
        for s in subs:
            if temp.get(s.key) is None:
                temp[s.key] = set()
            temp[s.key].add(s.id)

        result: set[BaseModel] = set()
        for key, ids in temp.items():
            getter = self._getter[key]
            entities = await getter(ids)
            result.add(entities)

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
