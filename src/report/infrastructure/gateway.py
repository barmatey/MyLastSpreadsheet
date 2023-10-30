from uuid import UUID

from src.core import Table
from src.report import domain
from src.report.services import SheetGateway
from src.spreadsheet.services import SheetService, NewSheetService
from src.spreadsheet import domain as sheet_domain


class SheetGatewayAPI(SheetGateway):
    def __init__(self, sheet_service: SheetService, new_service: NewSheetService):
        self._sheet_service = sheet_service
        self._new_service = new_service

    async def get_sheet_by_id(self, sheet_id: UUID) -> sheet_domain.Sheet:
        return await self._sheet_service.get_sheet_by_uuid(sheet_id)

    async def create_sheet(self, table: Table[domain.CellValue] = None) -> UUID:
        sheet = await self._sheet_service.create_sheet(table)
        return sheet.sf.id

    async def get_cell(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.Cell:
        cell = await self._sheet_service.get_cell_by_index(sheet_id, row_pos, col_pos)
        return cell

    async def update_cell(self, cell: domain.Cell):
        await self._sheet_service.update_cells([cell])

    async def append_rows_from_other_sheet(self, target_sheet_id:  UUID, data: sheet_domain.Sheet) -> None:
        await self._new_service.append_rows_from_sheet(target_sheet_id, data)

    async def merge_sheets(self, target: sheet_domain.Sheet, data: sheet_domain.Sheet,
                           merge_on: list[sheet_domain.ColSindex]) -> None:
        await self._new_service.merge_sheets(target, data, merge_on)

    async def append_rows_from_table(self, sheet_id: UUID, table: Table[domain.Cell]):
        await self._new_service.append_rows_from_table(sheet_id, table)

    async def delete_rows_from_position(self, sheet_id: UUID, from_pos: int, count: int):
        await self._sheet_service.delete_sindexes_from_position(sheet_id, from_pos, count, axis=0)

    async def group_new_row_data_with_sheet(self, sheet_id: UUID, table: Table[domain.Cell], on: list[int]):
        await self._new_service.group_new_data_with_sheet(sheet_id, table, on)

