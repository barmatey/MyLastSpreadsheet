from uuid import UUID

from ..cell.entity import CellValue, Cell
from ..sheet_info.entity import SheetInfo
from ..sindex.entity import RowSindex, ColSindex
from .entity import Sheet
from .repository import SheetRepo


async def create_sheet(table: list[list[CellValue]], sheet_repo: SheetRepo) -> Sheet:
    size = (len(table), len(table[0])) if len(table) else (0, 0)
    sheet_meta = SheetInfo(size=size)
    row_sindexes = [RowSindex(sheet_info=sheet_meta, position=i) for i in range(0, size[0])]
    col_sindexes = [ColSindex(sheet_info=sheet_meta, position=j) for j in range(0, size[1])]
    cells = []
    for i, row in enumerate(table):
        for j, cell_value in enumerate(row):
            cells.append(
                Cell(sheet_info=sheet_meta, row_sindex=row_sindexes[i], col_sindex=col_sindexes[j], value=cell_value))
    sheet = Sheet(sheet_info=sheet_meta, rows=row_sindexes, cols=col_sindexes, cells=cells)
    await sheet_repo.add(sheet)
    return sheet


async def get_by_uuid(uuid: UUID, sheet_repo: SheetRepo) -> Sheet:
    return await sheet_repo.get_by_uuid(uuid)
