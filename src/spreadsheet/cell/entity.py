from typing import Union, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.spreadsheet.sheet_info.entity import SheetMeta
from src.spreadsheet.sindex.entity import Sindex

CellValue = Union[int, float, str, bool, datetime, None]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(BaseModel):
    sheet: SheetMeta
    row_sindex: Sindex
    col_sindex: Sindex
    value: CellValue = None
    uuid: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"Cell"

    def __repr__(self):
        return f"Cell"

    def __hash__(self):
        return self.uuid.__hash__()
