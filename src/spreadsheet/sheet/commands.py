from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.bus.eventbus import Queue
from src.spreadsheet.sheet import entity as sheet_entity, events as sheet_events, usecases as sheet_usecases
from src.spreadsheet.sindex import entity as sindex_entity, handlers as sindex_services
from src.spreadsheet.cell import entity as cell_entity, handlers as cell_services


class AppendRows(BaseModel):
    sheet: sheet_entity.Sheet
    table: list[list[cell_entity.CellValue]]
    uuid: UUID = Field(default_factory=uuid4)

    def execute(self):
        sheet_usecases.append_rows(self.sheet, self.table)
