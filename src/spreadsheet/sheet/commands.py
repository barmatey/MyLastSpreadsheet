from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.bus.eventbus import Queue
from src.spreadsheet.sheet import entity as sheet_entity, events as sheet_events, usecases as sheet_usecases
from src.spreadsheet.sindex import entity as sindex_entity, usecases as sindex_usecases
from src.spreadsheet.cell import entity as cell_entity, handlers as cell_services


class AppendRows(BaseModel):
    sheet: sheet_entity.Sheet
    table: list[list[cell_entity.CellValue]]
    uuid: UUID = Field(default_factory=uuid4)

    def execute(self):
        sheet_usecases.append_rows(self.sheet, self.table)


class DeleteSindexes(BaseModel):
    sheet: sheet_entity.Sheet
    targets: list[sindex_entity.Sindex]
    uuid: UUID = Field(default_factory=uuid4)

    def execute(self):
        sheet = self.sheet
        direction = self.targets[0].direction
        for sindex in self.targets:
            if sindex.direction != direction:
                raise Exception
            sindex_usecases.delete_sindex(sindex)
        sindex_usecases.reindex(sheet, direction)
        sheet.size = (sheet.size[0] - len(self.targets), sheet.size[1])
        sheet_usecases.update_sheet(sheet)
