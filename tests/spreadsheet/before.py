import db
from src.my_spreadsheet import domain, commands, bootstrap


async def create_sheet(table: list[list[domain.CellValue]] = None) -> domain.Sheet:
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet_service = boot.get_sheet_service()
        cmd = commands.CreateSheet(table=table, receiver=sheet_service)
        sheet = await cmd.execute()
        await session.commit()
        return sheet
