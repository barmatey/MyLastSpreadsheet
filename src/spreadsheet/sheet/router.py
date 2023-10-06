import db
from src.spreadsheet.sheet.commands import CreateSheet
from src.spreadsheet.sheet.repository import SheetRepoPostgres

get_asession = db.get_async_session


async def create_sheet():
    async with get_asession() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = CreateSheet(sheet_repo=sheet_repo)
        sheet_id = await cmd.execute()
        await session.commit()
        return sheet_id
