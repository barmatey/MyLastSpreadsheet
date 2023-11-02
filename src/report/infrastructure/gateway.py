from uuid import UUID

from src.core import Table
from src.report import domain
from src.report.services import SheetGateway
from src.sheet import domain as sheet_domain, services as sheet_service


class SheetGatewayAPI(SheetGateway):
    def __init__(self, service: sheet_service.SheetService):
        self._sheet_service = service

    async def get_sheet_by_id(self, sheet_id: UUID) -> sheet_domain.Sheet:
        return await self._sheet_service.get_sheet_by_id(sheet_id)

    async def create_sheet(self, table: Table[domain.CellValue] = None) -> UUID:
        sheet = await self._sheet_service.create_sheet(table)
        return sheet.sf.id

    async def update_sheet(self, data: sheet_domain.Sheet):
        await self._sheet_service.update_sheet(data)

    async def merge_sheets(self, target_sheet_id: UUID, data: sheet_domain.Sheet, merge_on: list[int]):
        await self._sheet_service.complex_merge(target_sheet_id, data, merge_on, merge_on)
