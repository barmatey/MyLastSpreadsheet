from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import String, Integer, ForeignKey, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import helpers
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import Base
from src.spreadsheet.sindex.entity import Sindex, SindexDirection, RowSindex, ColSindex


class SindexRepo(ABC):
    @abstractmethod
    async def add(self, sindex: Sindex):
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, sindexes: list[Sindex]):
        raise NotImplemented

    @abstractmethod
    async def get_sheet_rows(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[RowSindex]:
        raise NotImplemented

    @abstractmethod
    async def get_sheet_cols(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[ColSindex]:
        raise NotImplemented


class RowSindexModel(Base):
    __tablename__ = "row_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: Sheet) -> RowSindex:
        return RowSindex(uuid=self.uuid, sheet=sheet, position=self.position)


class ColSindexModel(Base):
    __tablename__ = "col_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: Sheet) -> ColSindex:
        return ColSindex(uuid=self.uuid, sheet=sheet, position=self.position)


class SindexRepoPostgres(SindexRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sindex: Sindex):
        if isinstance(sindex, RowSindex):
            model = RowSindexModel
        elif isinstance(sindex, ColSindex):
            model = ColSindexModel
        else:
            raise ValueError
        model = model(uuid=sindex.uuid, position=sindex.position, sheet_uuid=sindex.sheet.uuid)
        self._session.add(model)

    async def remove_many(self, sindexes: list[Sindex]):
        model = RowSindexModel if isinstance(sindexes[0], RowSindex) else ColSindexModel
        uuids = [x.uuid for x in sindexes]
        stmt = delete(model).where(model.uuid.in_(uuids))
        await self._session.execute(stmt)

    async def get_sheet_rows(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[RowSindex]:
        orders = helpers.postgres.parse_order_by(RowSindexModel, order_by, asc)
        stmt = select(RowSindexModel).where(RowSindexModel.sheet_uuid == sheet.uuid).order_by(*orders)
        result = await self._session.execute(stmt)
        result = [x.to_entity(sheet) for x in result.scalars().fetchall()]
        return result

    async def get_sheet_cols(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[ColSindex]:
        orders = helpers.postgres.parse_order_by(ColSindexModel, order_by, asc)
        stmt = select(ColSindexModel).where(ColSindexModel.sheet_uuid == sheet.uuid).order_by(*orders)
        result = await self._session.execute(stmt)
        result = [x.to_entity(sheet) for x in result.scalars().fetchall()]
        return result
