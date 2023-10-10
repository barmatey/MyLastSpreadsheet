from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import entity as sheet_entity
from ..sheet_info import entity as sheet_info_entity
from ..sindex.repository import RowSindexModel, ColSindexModel, SindexRepoPostgres, SindexRepo
from ..cell.repository import CellModel, CellRepoPostgres, CellRepo
from ..sheet_info.repository import SheetInfoModel, SheetInfoRepoPostgres, SheetInfoRepo


class SheetRepo(ABC):
    @property
    def sheet_info_repo(self) -> SheetInfoRepo:
        raise NotImplemented

    @property
    def sindex_repo(self) -> SindexRepo:
        raise NotImplemented

    @property
    def cell_repo(self) -> CellRepo:
        raise NotImplemented

    @abstractmethod
    async def add(self, sheet: sheet_entity.Sheet):
        raise NotImplemented

    @abstractmethod
    async def get_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        raise NotImplemented


class SheetRepoPostgres(SheetRepo):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._sheet_info_repo = SheetInfoRepoPostgres(session)
        self._cell_repo = CellRepoPostgres(session)
        self._sindex_repo = SindexRepoPostgres(session)

    @property
    def sheet_info_repo(self) -> SheetInfoRepo:
        return self._sheet_info_repo

    @property
    def sindex_repo(self) -> SindexRepo:
        return self._sindex_repo

    @property
    def cell_repo(self) -> CellRepo:
        return self._cell_repo

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
            .where(SheetInfoModel.uuid == uuid)
        )
        result = list(await self._session.execute(stmt))
        if len(result) == 0:
            stmt = select(SheetInfoModel).where(SheetInfoModel.uuid == uuid)
            result = list(await self._session.execute(stmt))
            if len(result) != 1:
                raise LookupError
            return sheet_entity.Sheet(sheet_info=sheet_info_entity.SheetInfo(), rows=[], cols=[], cells=[])

        sheet_info: sheet_info_entity.SheetInfo = result[0][0].to_entity()
        rows = [result[x][1].to_entity(sheet_info)
                for x in range(0, sheet_info.size[0] * sheet_info.size[1], sheet_info.size[1])]
        cols = [result[x][2].to_entity(sheet_info) for x in range(0, sheet_info.size[1])]
        cells = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = i * sheet_info.size[1] + j
                cells.append(result[index][3].to_entity(sheet_info, row, col))

        sheet = sheet_entity.Sheet(sheet_info=sheet_info, rows=rows, cols=cols, cells=cells)
        return sheet
