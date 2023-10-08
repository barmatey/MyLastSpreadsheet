from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import entity as sheet_entity
from ..sindex import entity as sindex_entity
from ..sheet_info import entity as sheet_info_entity
from ..sindex.repository import RowSindexModel, ColSindexModel, SindexRepoPostgres
from ..cell.repository import CellModel, get_dtype, get_value, CellRepoPostgres
from ..sheet_info.repository import SheetInfoModel, SheetInfoRepoPostgres


class SheetRepo(ABC):
    async def add(self, sheet: sheet_entity.Sheet):
        raise NotImplemented

    async def get_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        raise NotImplemented


class SheetRepoPostgres(SheetRepo):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._sheet_info_repo = SheetInfoRepoPostgres(session)
        self._cell_repo = CellRepoPostgres(session)
        self._sindex_repo = SindexRepoPostgres(session)

    async def add(self, sheet: sheet_entity.Sheet):
        await self._sheet_info_repo.add(sheet.sheet_info)
        if len(sheet.rows) and len(sheet.cols) and len(sheet.cells):
            await self._sindex_repo.add_many(sheet.rows)
            await self._sindex_repo.add_many(sheet.cols)
            await self._cell_repo.add_many(sheet.cells)

    async def get_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        stmt = (
            select(SheetInfoModel, RowSindexModel, ColSindexModel, CellModel)
            .join(SheetInfoModel, CellModel.sheet_uuid == SheetInfoModel.uuid)
            .join(RowSindexModel, CellModel.row_sindex_uuid == RowSindexModel.uuid)
            .join(ColSindexModel, CellModel.col_sindex_uuid == ColSindexModel.uuid)
            .order_by(RowSindexModel.position, ColSindexModel.position)
            .where(CellModel.sheet_uuid == uuid)
        )
        result = list(await self._session.execute(stmt))
        sheet_info: sheet_info_entity.SheetInfo = result[0][0].to_entity()
        rows = [result[x][1].to_entity(sheet_info)
                for x in range(0, sheet_info.size[0]*sheet_info.size[1], sheet_info.size[1])]
        cols = [result[x][2].to_entity(sheet_info) for x in range(0, sheet_info.size[1])]
        cells = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = i * sheet_info.size[1] + j
                cells.append(result[index][3].to_entity(sheet_info, row, col))

        sheet = sheet_entity.Sheet(sheet_info=sheet_info, rows=rows, cols=cols, cells=cells)
        return sheet
