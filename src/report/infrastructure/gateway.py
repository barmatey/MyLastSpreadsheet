from uuid import UUID

from src.report import domain
from src.report.services import SheetGateway
from src.spreadsheet.services import SheetService


class SheetGatewayAPI(SheetGateway):
    def __init__(self, sheet_service: SheetService):
        self._sheet_service = sheet_service

    async def create_sheet(self, table: domain.Table = None) -> UUID:
        sheet = await self._sheet_service.create_sheet(table)
        return sheet.sf.id

    async def get_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.CellValue:
        raise NotImplemented

    async def update_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int, value: domain.CellValue):
        raise NotImplemented

    async def insert_row_from_position(self, sheet_id: UUID, from_pos: int, row: list[domain.CellValue]):
        await self._sheet_service.insert_sindexes_from_position(sheet_id, [row], from_pos, 0)

