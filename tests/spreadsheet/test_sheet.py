import pytest

import db
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    commands as sheet_commands,
    subscriber as sheet_subscriber,
    bootstrap as sheet_bootstrap,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    services as sindex_services,
    subscriber as sindex_subscriber,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
    services as cell_services,
    subscriber as cell_subscriber,
)
from tests.spreadsheet.before import create_sheet


@pytest.mark.asyncio
async def test_create_sheet():
    async with db.get_async_session() as session:
        cmd = sheet_commands.CreateSheet(table=[[0, 1], [2, 3], [4, 5]], bootstrap=sheet_bootstrap.Bootstrap(session))
        sheet: sheet_entity.Sheet = await cmd.execute()

        assert sheet.sheet_info.size == (3, 2)
        for i in range(0, 3):
            assert sheet.rows[i].position == i
        for i in range(0, 2):
            assert sheet.cols[i].position == i
        for i in range(0, 6):
            assert sheet.cells[i].value == i


@pytest.mark.asyncio
async def test_get_sheet_by_uuid():
    async with db.get_async_session() as session:
        sheet = await create_sheet(table=[[0, 1], [2, 3], [4, 5]])
        cmd = sheet_commands.GetSheetByUuid(uuid=sheet.sheet_info.uuid, bootstrap=sheet_bootstrap.Bootstrap(session))
        sheet_from_repo = await cmd.execute()
        assert sheet_from_repo == sheet


@pytest.mark.asyncio
async def test_sheet_changes_state_when_subscribe_to_another_sheet():
    sheet1 = await create_sheet([
        [11, 22],
    ])
    sheet2 = await create_sheet()

    async with db.get_async_session() as session:
        bootstrap = sheet_bootstrap.Bootstrap(session)
        await bootstrap.get_sheet_subscriber(sheet2).follow_sheet(sheet1)
        await bootstrap.get_event_bus().run()
        await session.commit()

    async with db.get_async_session() as session:
        bootstrap = sheet_bootstrap.Bootstrap(session)
        sheet2 = await sheet_commands.GetSheetByUuid(uuid=sheet2.sheet_info.uuid, bootstrap=bootstrap).execute()
        assert sheet2.sheet_info.size == (1, 2)
        assert len(sheet2.cells) == 2
        assert sheet2.cells[0].value == 11
        assert sheet2.cells[1].value == 22


@pytest.mark.asyncio
async def test_sheet_delete_sindex_when_parent_sindex_deleted():
    sheet1 = await create_sheet([
        [11, 22, 33],
        [44, 55, 66],
    ])
    sheet2 = await create_sheet()

    # Follow
    async with db.get_async_session() as session:
        bootstrap = sheet_bootstrap.Bootstrap(session)
        await bootstrap.get_sheet_subscriber(sheet2).follow_sheet(sheet1)
        await bootstrap.get_event_bus().run()
        await session.commit()

    # Delete
    async with db.get_async_session() as session:
        bootstrap = sheet_bootstrap.Bootstrap(session)
        await bootstrap.get_sheet_service().delete_sindexes([sheet1.rows[0]])
        await bootstrap.get_event_bus().run()
        await session.commit()

    # Assert
    async with db.get_async_session() as session:
        bootstrap = sheet_bootstrap.Bootstrap(session)
        actual = await sheet_commands.GetSheetByUuid(uuid=sheet2.sheet_info.uuid, bootstrap=bootstrap).execute()
        assert len(actual.rows) == 1
        assert actual.sheet_info.size == (1, 3)
