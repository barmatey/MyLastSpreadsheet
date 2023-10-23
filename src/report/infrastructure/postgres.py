from typing import Type
from uuid import UUID
from datetime import datetime
import pytz

from sortedcontainers import SortedList
from sqlalchemy import String, Integer, TIMESTAMP, func, Float, ForeignKey, select, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import helpers
from src.base.repo.postgres import Base, PostgresRepo
from src.base.repo.repository import Repository
from src.core import OrderBy

from src.report import domain, services


class SourceInfoModel(Base):
    __tablename__ = "source"
    title: Mapped[str] = mapped_column(String(32), nullable=False)
    wires = relationship('WireModel')
    reports = relationship('ReportModel')

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


class ReportModel(Base):
    __tablename__ = "report"
    title: Mapped[str] = mapped_column(String(64), default='default_title')
    start_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    freq: Mapped[str] = mapped_column(String(16), nullable=False)
    plan_items: Mapped[JSON] = mapped_column(JSON, nullable=False)
    sheet_id: Mapped[UUID] = mapped_column(String(64), nullable=False)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("source.id"))

    def to_entity(self) -> domain.Report:
        raise NotImplemented

    @staticmethod
    def to_entity_from_tuple(data) -> domain.Report:
        report_model: ReportModel = data[0]
        source_info_model: SourceInfoModel = data[1]
        pl = domain.PlanItems(
            ccols=report_model.plan_items.get('ccols'),
            uniques=report_model.plan_items.get('uniques'),
            order=SortedList(report_model.plan_items.get('order')),
        )
        return domain.Report(
            title=report_model.title,
            category="PROFIT",
            id=report_model.id,
            plan_items=pl,
            source_info=source_info_model.to_entity(),
            sheet_info=domain.SheetInfo(id=report_model.sheet_id),
            interval=domain.Interval(start_date=report_model.start_date, end_date=report_model.end_date,
                                     freq=report_model.freq)
        )

    @classmethod
    def from_entity(cls, entity: domain.Report):
        return cls(
            title=entity.title,
            id=entity.id,
            plan_items=entity.plan_items.model_dump(),
            sheet_id=str(entity.sheet_info.id),
            source_id=entity.source_info.id,
            **entity.interval.model_dump(),
        )


class SourceInfoRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SourceInfoModel):
        super().__init__(session, model)


class WireRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = WireModel):
        super().__init__(session, model)

    async def get_one_by_id(self, uuid: UUID) -> domain.Wire:
        raise NotImplemented

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[domain.Wire]:
        stmt = (
            select(WireModel, SourceInfoModel)
            .join(SourceInfoModel, WireModel.source_id == SourceInfoModel.id)
            .where(WireModel.id.in_(ids))
        )
        result = await self._session.execute(stmt)
        entities = [x[0].to_entity(source_info=x[1].to_entity()) for x in result]
        return entities

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list[domain.Wire]:
        stmt = (
            select(WireModel, SourceInfoModel)
            .join(SourceInfoModel, WireModel.source_id == SourceInfoModel.id)
        )
        stmt = self._expand_statement(stmt, filter_by, order_by, slice_from, slice_to)
        result = await self._session.execute(stmt)
        entities = [x[0].to_entity(source_info=x[1].to_entity()) for x in result]
        return entities

    async def get_uniques(self, columns_by: list[str], filter_by: dict = None,
                          order_by: OrderBy = None) -> list[domain.Wire]:
        stmt = (
            select(WireModel, SourceInfoModel)
            .join(SourceInfoModel, WireModel.source_id == SourceInfoModel.id)
            .distinct(*[self._model.__table__.c[col] for col in columns_by])
        )
        stmt = self._expand_statement(stmt, filter_by, order_by)
        result = await self._session.execute(stmt)
        entities = [x[0].to_entity(source_info=x[1].to_entity()) for x in result]
        return entities


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


class ReportRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = ReportModel):
        super().__init__(session, model)

    async def get_one_by_id(self, uuid: UUID) -> domain.Report:
        raise NotImplemented

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[domain.Report]:
        raise NotImplemented

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list[domain.Report]:
        stmt = (
            select(ReportModel, SourceInfoModel)
            .join(SourceInfoModel, SourceInfoModel.id == ReportModel.source_id)
        )
        stmt = self._expand_statement(stmt, filter_by, order_by, slice_from, slice_to)
        data = await self._session.execute(stmt)
        reports = [ReportModel.to_entity_from_tuple(x) for x in data]
        return reports

