from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.spreadsheet.sheet import entity as sheet_entity, handlers as sheet_services
from src.spreadsheet.sindex import entity as sindex_entity, handlers as sindex_services
from src.spreadsheet.cell import entity as cell_entity, handlers as cell_services


class AppendRows(BaseModel):
    sheet: sheet_entity.Sheet
    table: list[list[cell_entity.CellValue]]
    uuid: UUID = Field(default_factory=uuid4)

    def execute(self):
        table = self.table
        sheet = self.sheet
        if len(table) == 0:
            raise Exception
        if sheet.size == (0, 0):
            sheet.size = (0, len(table[0]))

        for i, row in enumerate(table):
            if len(row) != self._entity.size[1]:
                raise Exception
            for j, cell_value in enumerate(row):
                cell_services.create_cell(sheet=sheet, value=table[i][j])

        sheet.size = (self._entity.size[0] + len(table), self._entity.size[1])
        sheet_services.update_sheet(sheet)
