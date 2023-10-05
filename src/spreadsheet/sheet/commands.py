from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet.entity import Sheet


class AppendRows(BaseModel):
    sheet: Sheet
    table: list[list[CellValue]]
    uuid: UUID = Field(default_factory=uuid4)

    def execute(self):
        pass