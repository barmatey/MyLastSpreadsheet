from uuid import UUID

import db
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.cell.repository import CellRepoPostgres
from src.spreadsheet.sheet import commands as sheet_commands
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepoPostgres

get_asession = db.get_async_session


async def create_sheet():
    async with get_asession() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(sheet_repo=sheet_repo)
        sheet_id = await cmd.execute()
        await session.commit()
        return sheet_id


async def get_sheet(uuid: UUID) -> Sheet:
    async with get_asession() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.GetSheet(uuid=uuid, sheet_repo=sheet_repo)
        sheet = await cmd.execute()
        return sheet



# async def append_rows(sheet: Sheet, table: list[list[CellValue]]):
#     async with get_asession() as session:
#         sheet_repo = SheetRepoPostgres(session)
#         sindex_repo = SindexRepoPostgres(session)
#         cell_repo = CellRepoPostgres(session)
#         cmd = AppendRows(sheet_repo=sheet_repo, sindex_repo=sindex_repo, cell_repo=cell_repo, sheet=sheet, table=table)
#         await cmd.execute()
