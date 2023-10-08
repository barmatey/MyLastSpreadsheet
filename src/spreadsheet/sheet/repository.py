from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from . import entity as sheet_entity
from ..sindex import entity as sindex_entity
from ..sindex.repository import RowSindexModel, ColSindexModel
from ..cell.repository import CellModel, get_dtype, get_value
from ..sheet_info.repository import SheetInfoModel


class SheetRepo(ABC):
    async def add(self, sheet: sheet_entity.Sheet):
        raise NotImplemented

    async def get_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        raise NotImplemented


class SheetRepoPostgres(SheetRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sheet: sheet_entity.Sheet):
        sheet_info = SheetInfoModel(**sheet.sheet_info.model_dump())
        self._session.add(sheet_info)

        data = [{"uuid": x.uuid, "position": x.position, "sheet_uuid": x.sheet.uuid} for x in sheet.rows]
        stmt = insert(RowSindexModel)
        await self._session.execute(stmt, data)

        data = [{"uuid": x.uuid, "position": x.position, "sheet_uuid": x.sheet.uuid} for x in sheet.cols]
        stmt = insert(ColSindexModel)
        await self._session.execute(stmt, data)
