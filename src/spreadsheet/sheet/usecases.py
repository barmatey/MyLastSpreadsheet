from uuid import UUID

from src.bus.eventbus import Queue
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepo, SheetRepoFake
from src.spreadsheet.cell import usecases as cell_usecases
from src.spreadsheet.sheet import events as sheet_events


def create_sheet(repo: SheetRepo = SheetRepoFake()) -> UUID:
    sheet = Sheet()
    repo.add(sheet)
    return sheet.uuid


def update_sheet(sheet: Sheet, repo: SheetRepo = SheetRepoFake()):
    repo.update(sheet)


def append_rows(sheet: Sheet, table: list[list[CellValue]], repo: SheetRepo = SheetRepoFake()):
    sheet = sheet.model_copy()
    if len(table) == 0:
        raise Exception
    if sheet.size == (0, 0):
        sheet.size = (0, len(table[0]))

    for i, row in enumerate(table):
        if len(row) != sheet.size[1]:
            raise Exception
        for j, cell_value in enumerate(row):
            cell_usecases.create_cell(sheet=sheet, value=table[i][j])

    sheet.size = (sheet.size[0] + len(table), sheet.size[1])
    repo.update(sheet)
    Queue().append(sheet_events.SheetRowsAppended(table=table))
