from typing import Type
from uuid import UUID

from sqlalchemy import String, Integer, TIMESTAMP, func, Float, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.repo.postgres import Base, PostgresRepo
from src.base.repo.repository import Repository, T

from src.report import domain, services


class SourceInfoModel(Base):
    __tablename__ = "source"
    title: Mapped[str] = mapped_column(String(32), nullable=False)
    wires = relationship('WireModel')

    def to_entity(self) -> domain.SourceInfo:
        return domain.SourceInfo(id=self.id, title=self.title)

    @classmethod
    def from_entity(cls, entity: domain.SourceInfo):
        return cls(
            id=entity.id,
            title=entity.title,
        )


class WireModel(Base):
    __tablename__ = "wire"
    date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    sender: Mapped[float] = mapped_column(Float, nullable=False)
    receiver: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    sub1: Mapped[str] = mapped_column(String(1024), default="")
    sub2: Mapped[str] = mapped_column(String(1024), default="")
    source_id: Mapped[UUID] = mapped_column(ForeignKey("source.id"))

    def to_entity(self, **kwargs) -> domain.Wire:
        return domain.Wire(
            id=self.id,
            sender=self.sender,
            receiver=self.receiver,
            amount=self.amount,
            sub1=self.sub1,
            sub2=self.sub2,
            date=self.date,
        )

    @classmethod
    def from_entity(cls, entity: domain.Wire):
        return cls(
            id=entity.id,
            sender=entity.sender,

        )


class SourceInfoRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SourceInfoModel):
        super().__init__(session, model)


class WireRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = WireModel):
        super().__init__(session, model)


class SourceFullRepo(services.SourceRepo):
    def __init__(self, session: AsyncSession):
        self._source_info_repo = SourceInfoRepo(session)
        self._wire_repo = WireRepo(session)
        self._session = session

    @property
    def source_info_repo(self) -> Repository[domain.SourceInfo]:
        return self._source_info_repo

    @property
    def wire_repo(self) -> Repository[domain.Wire]:
        return self._wire_repo

    async def add_source(self, source: domain.Source):
        await self.source_info_repo.add_many([source.source_info])
        await self.wire_repo.add_many(source.wires)

    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        stmt = (select(SourceInfoModel, WireModel)
                .join(WireModel, WireModel.source_id == SourceInfoModel.id)
                .where(SourceInfoModel.id == uuid)
                )
        result = await self._session.execute(stmt)
        result = list(result)

        if len(result) == 0:
            stmt = select(SourceInfoModel).where(SourceInfoModel.id == uuid)
            result = await self._session.scalar(stmt)
            source_info = result.to_entity()
            return domain.Source(source_info=source_info)
        else:
            raise NotImplemented
