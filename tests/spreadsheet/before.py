import db
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet.commands import CreateSheet
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepoPostgres


async def create_sheet(table: list[list[CellValue]] = None) -> Sheet:
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = CreateSheet(table=table, sheet_repo=sheet_repo, )
        sheet = await cmd.execute()
        await session.commit()
        return sheet
