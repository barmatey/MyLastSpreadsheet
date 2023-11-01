from . import domain


class SheetService:
    def __init__(self, repo):
        self._repo = repo

    async def create_sheet(self, sheet: domain.Sheet = None) -> domain.Sheet:
        if sheet is None:
            sheet = domain.Sheet(sf=domain.SheetInfo(title=""))
        await self._repo.add(sheet)
        return sheet
