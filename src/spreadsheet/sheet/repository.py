from abc import ABC, abstractmethod
from uuid import UUID

from . import entity as sheet_entity
from ..sindex.repository import RowSindexModel, ColSindexModel
from ..cell.repository import CellModel, get_dtype, get_value
from ..sheet_info.repository import SheetInfoModel

class SheetRepo(ABC):
    async def add(self, sheet: sheet_entity.Sheet):
        raise NotImplemented

    async def get_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        raise NotImplemented


class SheetRepoPostgres(SheetRepo):
    async def add(self, sheet: sheet_entity.Sheet):

