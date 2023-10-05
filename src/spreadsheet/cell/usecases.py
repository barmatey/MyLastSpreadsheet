from uuid import UUID, uuid4

from src.spreadsheet.cell.entity import CellValue, Cell


def create_cell(value: CellValue, uuid: UUID = None) -> UUID:
    if uuid is None:
        uuid = uuid4()
    cell = Cell(value=value, uuid=uuid)