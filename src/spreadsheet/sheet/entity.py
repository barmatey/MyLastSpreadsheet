from pydantic import BaseModel

from src.spreadsheet.cell.entity import Cell
from src.spreadsheet.sheet_info.entity import SheetInfo
from src.spreadsheet.sindex.entity import RowSindex, ColSindex


class Sheet(BaseModel):
    sheet_info: SheetInfo
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]
