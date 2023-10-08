import random

import pytest
import pytest_asyncio

import db
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet.repository import SheetRepoPostgres
from src.spreadsheet.sheet import (entity as sheet_entity, commands as sheet_commands)


async def create_sheet(table: list[list[CellValue]]) -> sheet_entity.Sheet:
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(table=table, sheet_repo=sheet_repo, )
        sheet = await cmd.execute()
        await session.commit()
        return sheet


@pytest.mark.asyncio
async def test_create_sheet():
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(table=[[0, 1], [2, 3], [4, 5]], sheet_repo=sheet_repo, )
        sheet = await cmd.execute()

        assert sheet.sheet_info.size == (3, 2)
        for i in range(0, 6):
            assert sheet.cells[i].value == i


@pytest.mark.asyncio
async def test_get_sheet_by_uuid():
    sheet = await create_sheet(table=[[0, 1], [2, 3], [4, 5]])
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.GetSheetByUuid(uuid=sheet.sheet_info.uuid, sheet_repo=sheet_repo)
        sheet_from_repo = await cmd.execute()
        assert sheet_from_repo == sheet

