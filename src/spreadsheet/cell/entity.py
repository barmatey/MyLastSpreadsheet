from typing import Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.spreadsheet.sheet.entity import Sheet

CellValue = Union[int, float, str, bool, datetime, None]


class Cell(BaseModel):
    sheet: Sheet
    value: CellValue = None
    uuid: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"Cell(uuid={self.uuid})"

    def __repr__(self):
        return f"Cell(uuid={self.uuid})"

    def __hash__(self):
        return self.uuid.__hash__()


