from typing import Type
from uuid import UUID

from sqlalchemy import String, Integer, TIMESTAMP, func, Float, ForeignKey, select, JSON
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

    def to_entity(self, source_info: domain.SourceInfo) -> domain.Wire:
        return domain.Wire(
            id=self.id,
            sender=self.sender,
            receiver=self.receiver,
            amount=self.amount,
            sub1=self.sub1,
            sub2=self.sub2,
            date=self.date,
            source_info=source_info
        )

    @classmethod
    def from_entity(cls, entity: domain.Wire):
        return cls(
            id=entity.id,
            sender=entity.sender,
            receiver=entity.receiver,
            amount=entity.amount,
            sub1=entity.sub1,
            sub2=entity.sub2,
            date=entity.date,
            source_id=entity.source_info.id,
        )


class GroupModel(Base):
    __tablename__ = "group"
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("source.id"))
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    plan_items: Mapped[JSON] = mapped_column(JSON, nullable=False)

    def to_entity(self, source_info: domain.SourceInfo) -> domain.Group:
        return domain.Group(
            id=self.id,
            title=self.title,
            sheet_info=domain.SheetInfo(id=self.sheet_id),
            source_info=source_info,
            plan_items=domain.PlanItems(**self.plan_items)
        )

    @classmethod
    def from_entity(cls, entity: domain.Group):
        return cls(
            id=entity.id,
            title=entity.title,
            source_id=entity.source_info.id,
            sheet_id=entity.sheet_info.id,
            plan_items=entity.plan_items.model_dump(),
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
            source_info = result[0][0].to_entity()
            wires = [x[1].to_entity(source_info=source_info) for x in result]
            return domain.Source(source_info=source_info, wires=wires)


class GroupRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = GroupModel):
        super().__init__(session, model)

    async def get_one_by_id(self, uuid: UUID) -> T:
        # stmt = (
        #     select(GroupModel, SourceInfoModel)
        #     .join(SourceInfoModel, GroupModel.source_id == SourceInfoModel.id)
        #     .where(GroupModel.id == uuid)
        # )
        raise NotImplemented
