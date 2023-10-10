from pydantic import BaseModel

from src.spreadsheet.cell.entity import Cell
from src.spreadsheet.sheet_info.entity import SheetInfo
from src.spreadsheet.sindex.entity import RowSindex, ColSindex


class Sheet(BaseModel):
    sheet_info: SheetInfo
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]

    def __hash__(self):
        return self.sheet_info.uuid.__hash__()

    def __eq__(self, other: 'Sheet'):
        if self.sheet_info != other.sheet_info:
            return False
        if len(self.rows) != len(other.rows):
            return False
        for left, right in zip(self.rows, other.rows):
            if left != right:
                return False
        if len(self.cols) != len(other.cols):
            return False
        for left, right in zip(self.cols, other.cols):
            if left != right:
                return False
        if len(self.cells) != len(other.cells):
            return False
        for left, right in zip(self.cells, other.cells):
            if left != right:
                return False
        return True
