from abc import abstractmethod, ABC
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, ForeignKey, delete, select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src import helpers
from src.core import OrderBy
from src.spreadsheet.cell.entity import Cell, CellValue, CellDtype
from src.spreadsheet.sheet_info.entity import SheetInfo
from src.spreadsheet.sheet_info.repository import Base
from src.spreadsheet.sindex.entity import RowSindex, ColSindex
from src.spreadsheet.sindex.repository import RowSindexModel, ColSindexModel


class CellRepo(ABC):
    @abstractmethod
    async def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    async def add_many(self, cells: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def get_many_by_sheet_filters(self, sheet_info: SheetInfo, rows: list[RowSindex] = None,
                                        cols: list[ColSindex] = None,
                                        order_by: OrderBy = None) -> list[Cell]:
        raise NotImplemented

    @abstractmethod
    async def update_one(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, cells: list[Cell]):
        raise NotImplemented









class CellRepoPostgres(CellRepo):
    def __init__(self, session: AsyncSession):
        self._session = session



    async def get_many_by_sheet_filters(self, sheet_info: SheetInfo, rows: list[RowSindex] = None,
                                        cols: list[ColSindex] = None,
                                        order_by: OrderBy = None) -> list[Cell]:
        stmt = (
            select(CellModel, RowSindexModel, ColSindexModel)
            .join(RowSindexModel, CellModel.row_sindex_uuid == RowSindexModel.uuid)
            .join(ColSindexModel, CellModel.col_sindex_uuid == ColSindexModel.uuid)
            .where(CellModel.sheet_uuid == sheet_info.uuid)
        )
        if rows:
            stmt = stmt.where(CellModel.row_sindex_uuid.in_([x.uuid for x in rows]))
        if cols:
            stmt = stmt.where(CellModel.col_sindex_uuid.in_([x.uuid for x in cols]))
        if order_by:
            orders = helpers.postgres.parse_order_by(CellModel, *order_by)
            stmt = stmt.order_by(*orders)

        result = await self._session.execute(stmt)
        result = [x[0].to_entity(sheet_info, row=x[1].to_entity(sheet_info), col=x[2].to_entity(sheet_info))
                  for x in result]
        return result

