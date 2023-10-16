from uuid import UUID

from ...spreadsheet.services import SheetService
from .. import services, domain


class GroupGatewayService(services.GroupGateway):
    def __init__(self, sheet_service: SheetService):
        self._sheet_service = sheet_service

    async def create_sheet(self, table: list[list[domain.CellValue]]) -> UUID:
        sheet = await self._sheet_service.create_sheet(table)
        return sheet.sf.id
