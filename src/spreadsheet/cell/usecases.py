from uuid import UUID, uuid4

from src.bus.eventbus import Queue
from src.spreadsheet.cell.entity import CellValue, Cell
from src.spreadsheet.cell.repository import CellRepo
from src.spreadsheet.sheet_info.entity import SheetInfo
from src.spreadsheet.sindex.entity import Sindex
from . import events as cell_events


async def create_cell(sheet: SheetInfo, row: Sindex, col: Sindex, value: CellValue, repo: CellRepo, uuid: UUID = None) -> Cell:
    if uuid is None:
        uuid = uuid4()
    cell = Cell(sheet_info=sheet, row_sindex=row, col_sindex=col, value=value, uuid=uuid)
    await repo.add(cell)
    return cell


async def delete_cells(cells: list[Cell], repo: CellRepo):
    await repo.remove_many(cells)
    for cell in cells:
        Queue().append(cell_events.CellDeleted(entity=cell))
