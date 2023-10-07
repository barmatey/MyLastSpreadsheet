from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from src.bus.eventbus import Queue
from src.core import PydanticModel
from src.spreadsheet.sheet import (entity as sheet_entity, events as sheet_events, usecases as sheet_usecases,
                                   repository as sheet_repo)
from src.spreadsheet.sindex import (entity as sindex_entity, usecases as sindex_usecases, repository as sindex_repo)
from src.spreadsheet.cell import (entity as cell_entity, usecases as cell_usecases, repository as cell_repo)


class CreateSheet(PydanticModel):
    sheet_repo: sheet_repo.SheetRepo
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self) -> sheet_entity.Sheet:
        sheet = await sheet_usecases.create_sheet(self.sheet_repo)
        return sheet


class GetSheet(PydanticModel):
    sheet_repo: sheet_repo.SheetRepo
    uuid: UUID

    async def execute(self) -> sheet_entity.Sheet:
        return await sheet_usecases.get_sheet_by_uuid(self.uuid, self.sheet_repo)


class AppendRows(PydanticModel):
    sheet_repo: sheet_repo.SheetRepo
    sindex_repo: sindex_repo.SindexRepo
    cell_repo: cell_repo.CellRepo
    sheet: sheet_entity.Sheet
    table: list[list[cell_entity.CellValue]]
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self):
        table = self.table
        sheet = self.sheet.model_copy(deep=True)
        if len(table) == 0:
            raise Exception
        if sheet.size == (0, 0):
            sheet.size = (0, len(table[0]))

        for i, row in enumerate(table):
            if len(row) != sheet.size[1]:
                raise Exception
            row_sindex = await sindex_usecases.create_sindex(sheet, i+sheet.size[0], "ROW", self.sindex_repo)
            for j, cell_value in enumerate(row):
                col_sindex = await sindex_usecases.create_sindex(sheet, j, "COL", self.sindex_repo)
                _cell = await cell_usecases.create_cell(sheet, row_sindex, col_sindex, table[i][j], self.cell_repo)

        sheet.size = (sheet.size[0] + len(table), sheet.size[1])
        await sheet_usecases.update_sheet(sheet, self.sheet_repo)
        Queue().append(sheet_events.SheetRowsAppended(table=table))


class DeleteSindexes(PydanticModel):
    sheet: sheet_entity.Sheet
    sindexes: list[sindex_entity.Sindex]
    cells: list[cell_entity.Cell]
    uuid: UUID = Field(default_factory=uuid4)
    sheet_repo: sheet_repo.SheetRepo
    sindex_repo: sindex_repo.SindexRepo
    cell_repo: cell_repo.CellRepo

    async def execute(self):
        await cell_usecases.delete_cells(self.cells, self.cell_repo)
        await sindex_usecases.delete_sindexes(self.sindexes, self.sindex_repo)
        await sindex_usecases.reindex_rows(self.sheet, self.sindex_repo)

