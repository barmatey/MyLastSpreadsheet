from uuid import UUID, uuid4

from src.spreadsheet.cell.entity import CellValue, Cell
from src.spreadsheet.cell.repository import CellRepo, CellRepoFake
from src.spreadsheet.sheet.entity import Sheet


def create_cell(sheet: Sheet, value: CellValue, uuid: UUID = None, repo: CellRepo = CellRepoFake()) -> UUID:
    if uuid is None:
        uuid = uuid4()
    cell = Cell(sheet=sheet, value=value, uuid=uuid)
    repo.add(cell)
    return cell.uuid
