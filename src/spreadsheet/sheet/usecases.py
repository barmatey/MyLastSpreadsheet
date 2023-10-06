from uuid import UUID

from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepo


async def create_sheet(repo: SheetRepo) -> UUID:
    sheet = Sheet()
    await repo.add(sheet)
    return sheet.uuid


async def get_sheet_by_uuid(uuid: UUID, repo: SheetRepo) -> Sheet:
    return await repo.get_one_by_uuid(uuid)


async def update_sheet(sheet: Sheet, repo: SheetRepo):
    await repo.update(sheet)
