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

