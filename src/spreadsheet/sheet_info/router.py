from uuid import UUID

import db
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.cell.repository import CellRepoPostgres
from src.spreadsheet.sheet_info import commands as sheet_commands
from src.spreadsheet.sheet_info.entity import SheetMeta
from src.spreadsheet.sheet_info.repository import SheetInfoRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepoPostgres

get_asession = db.get_async_session


async def create_sheet():
    async with get_asession() as session:
        sheet_repo = SheetInfoRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(sheet_repo=sheet_repo)
        sheet_id = await cmd.execute()
        await session.commit()
        return sheet_id


async def get_sheet(uuid: UUID) -> SheetMeta:
    async with get_asession() as session:
        sheet_repo = SheetInfoRepoPostgres(session)
        cmd = sheet_commands.GetSheet(uuid=uuid, sheet_repo=sheet_repo)
        sheet = await cmd.execute()
        return sheet


async def append_rows(sheet: SheetMeta, table: list[list[CellValue]]):
    async with get_asession() as session:
        sheet_repo = SheetInfoRepoPostgres(session)
        sindex_repo = SindexRepoPostgres(session)
        cell_repo = CellRepoPostgres(session)
        cmd = sheet_commands.AppendRows(sheet_repo=sheet_repo, sindex_repo=sindex_repo, cell_repo=cell_repo, sheet=sheet, table=table)
        await cmd.execute()
        await session.commit()
