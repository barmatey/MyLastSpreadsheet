from typing import Type
from uuid import UUID

from sqlalchemy import String, Integer, TIMESTAMP, func, Float, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.repo.postgres import Base, PostgresRepo
from src.base.repo.repository import Repository, T

from src.report import domain, services


class SourceModel(Base):
    __tablename__ = "source"
    title: Mapped[str] = mapped_column(String(32), nullable=False)
    wires = relationship('WireModel')

    def to_entity(self, wires: list[domain.Wire]) -> domain.Source:
        return domain.Source(id=self.id, title=self.title, wires=wires)

    @classmethod
    def from_entity(cls, entity: domain.Source):
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


class SourceRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SourceModel):
        super().__init__(session, model)

    def get_one_by_id(self, uuid: UUID) -> T:
        stmt = (select(SourceModel, WireModel)
                .join(WireModel, WireModel.source_id == SourceModel.id)
                .where(SourceModel.id == uuid)
                )
        raise NotImplemented


class WireRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = WireModel):
        super().__init__(session, model)


class SourceFullRepo(services.SourceRepo):
    def __init__(self, session: AsyncSession):
        self._source_repo = SourceRepo(session)
        self._wire_repo = WireRepo(session)

    @property
    def source_repo(self) -> Repository[domain.Source]:
        return self._source_repo

    @property
    def wire_repo(self) -> Repository[domain.Wire]:
        return self._wire_repo
