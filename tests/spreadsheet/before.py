import asyncio
import inspect
import db
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    commands as sheet_commands,
    bootstrap as sheet_bootstrap,
)


async def create_sheet(table: list[list[CellValue]] = None) -> sheet_entity.Sheet:
    async with db.get_async_session() as session:
        bus = sheet_bootstrap.Bootstrap(session).get_event_bus()
        cmd = sheet_commands.CreateSheet(table=table, bus=bus)
        sheet = await cmd.execute()
        await session.commit()
        return sheet
