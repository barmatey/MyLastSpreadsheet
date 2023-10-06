from uuid import UUID, uuid4

from src.spreadsheet.cell.entity import CellValue, Cell
from src.spreadsheet.cell.repository import CellRepo
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.entity import Sindex


async def create_cell(sheet: Sheet, row: Sindex, col: Sindex, value: CellValue, repo: CellRepo, uuid: UUID = None) -> Cell:
    if uuid is None:
        uuid = uuid4()
    cell = Cell(sheet=sheet, row_sindex=row, col_sindex=col, value=value, uuid=uuid)
    await repo.add(cell)
    return cell
