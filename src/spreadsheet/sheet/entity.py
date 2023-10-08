from pydantic import BaseModel

from src.spreadsheet.cell.entity import Cell
from src.spreadsheet.sheet_meta.entity import SheetMeta
from src.spreadsheet.sindex.entity import RowSindex, ColSindex


class Sheet(BaseModel):
    sheet_meta: SheetMeta
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]
