from uuid import UUID

from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepo, SheetRepoFake


async def create_sheet(repo: SheetRepo = SheetRepoFake()) -> UUID:
    sheet = Sheet()
    await repo.add(sheet)
    return sheet.uuid


def update_sheet(sheet: Sheet, repo: SheetRepo = SheetRepoFake()):
    repo.update(sheet)





