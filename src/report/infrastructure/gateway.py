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

    async def get_cell(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.Cell:
        cell = await self._sheet_service.get_cell_by_index(sheet_id, row_pos, col_pos)
        return cell

    async def update_cell(self, cell: domain.Cell):
        await self._sheet_service.update_cells([cell])

    async def insert_row_from_position(self, sheet_id: UUID, from_pos: int, row: list[domain.CellValue]):
        await self._sheet_service.insert_sindexes_from_position(sheet_id, [row], from_pos, 0)

