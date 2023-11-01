from uuid import UUID

from . import domain


class UpdateSheetFromDifference:
    async def update(self, diff: domain.SheetDifference):
        raise NotImplemented


class SheetService:
    def __init__(self, repo):
        self._repo = repo

    async def create_sheet(self, sheet: domain.Sheet = None) -> domain.Sheet:
        if sheet is None:
            sheet = domain.Sheet(sf=domain.SheetInfo(title=""))
        await self._repo.add(sheet)
        return sheet

    async def get_by_id(self, sheet_id: UUID) -> domain.Sheet:
        return await self._repo.get_by_id(sheet_id)

    async def update_sheet(self, sheet: domain.Sheet) -> None:
        old_sheet = await self._repo.get_by_id(sheet.sf.id)
        diff = domain.SheetDifference.from_sheets(old_sheet, sheet)
        await UpdateSheetFromDifference().update(diff)

