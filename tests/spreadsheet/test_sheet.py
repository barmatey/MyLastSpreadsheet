import pytest
from loguru import logger

import db

from src.spreadsheet import domain, commands, bootstrap, services
from tests.spreadsheet.before import create_sheet


@pytest.mark.asyncio
async def test_create_sheet():
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        bus = boot.get_event_bus()
        sheet_service = boot.get_sheet_service()

        cmd = commands.CreateSheet(table=[[0, 1], [2, 3], [4, 5]], receiver=sheet_service)
        sheet: domain.Sheet = await cmd.execute()
        await bus.run()

        assert sheet.sf.size == (3, 2)
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
        boot = bootstrap.Bootstrap(session)
        sheet_service = boot.get_sheet_service()
        cmd = commands.GetSheetByUuid(uuid=sheet.sf.id, receiver=sheet_service)
        sheet_from_repo = await cmd.execute()
        assert sheet_from_repo == sheet


@pytest.mark.asyncio
async def test_sheet_changes_state_when_subscribe_to_another_sheet():
    sheet1 = await create_sheet([
        [11, 22],
    ])
    sheet2 = await create_sheet()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_subfac().create_sheet_subscriber(sheet2).follow_sheet(sheet1)
        await boot.get_event_bus().run()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet2 = await commands.GetSheetByUuid(uuid=sheet2.sf.id, receiver=boot.get_sheet_service()).execute()
        assert sheet2.sf.size == (1, 2)
        assert len(sheet2.cells) == 2
        assert sheet2.cells[0].value == 11
        assert sheet2.cells[1].value == 22


@pytest.mark.asyncio
async def test_child_sindex_reacts_on_parent_sindex_deleted():
    sheet1 = await create_sheet([
        [11, 22, 33],
        [44, 55, 66],
    ])
    sheet2 = await create_sheet()

    # Follow
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_subfac().create_sheet_subscriber(sheet2).follow_sheet(sheet1)
        await boot.get_event_bus().run()
        await session.commit()

    # Delete
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_sheet_service().delete_sindexes([sheet1.rows[0]])
        await boot.get_sheet_service().delete_sindexes([sheet1.cols[2]])
        await boot.get_event_bus().run()
        await session.commit()

    # Assert
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet_service = boot.get_sheet_service()
        actual = await commands.GetSheetByUuid(uuid=sheet2.sf.id, receiver=sheet_service).execute()
        assert actual.sf.size == (1, 2)
        assert actual.cells[0].value == 44
        assert actual.cells[1].value == 55
        assert actual.rows[0].position == 0


@pytest.mark.asyncio
async def test_insert_rows():
    sheet1 = await create_sheet([
        [22, 33],
        [55, 66],
    ])

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet_service = boot.get_sheet_service()
        await commands.InsertRows(id=sheet1.sf.id, receiver=sheet_service, table=[[1234, 123]],
                                  before_sindex=sheet1.rows[0]).execute()
        await commands.InsertCols(id=sheet1.sf.id, receiver=sheet_service, table=[[123, 11, 44]],
                                  before_sindex=sheet1.cols[0]).execute()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet = await commands.GetSheetByUuid(uuid=sheet1.id, receiver=boot.get_sheet_service()).execute()
        assert sheet.sf.size == (3, 3)
        for i, row in enumerate(sheet.rows):
            assert row.position == i
        assert sheet.cells[0].value == 123
        assert sheet.cells[1].value == 1234
        assert sheet.cells[2].value == 123
        assert sheet.cells[3].value == 11
        assert sheet.cells[4].value == 22
        assert sheet.cells[5].value == 33
        assert sheet.cells[6].value == 44
        assert sheet.cells[7].value == 55
        assert sheet.cells[8].value == 66


@pytest.mark.asyncio
async def test_expand_rows():
    sheet1 = await create_sheet([[1, 2], [11, 22], [111, 222, ]])
    sheet2 = await create_sheet([[None, None], [None, None], [None, None]])

    # Follow
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_subfac().create_cell_subscriber(sheet2.cells[0]).follow_cells([sheet1.cells[0]])
        await boot.get_subfac().create_cell_subscriber(sheet2.cells[1]).follow_cells([sheet1.cells[1]])
        await boot.get_event_bus().run()
        await session.commit()

    # Expand
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet2 = await boot.get_sheet_service().get_sheet_by_uuid(sheet2.sf.id)
        await boot.get_expand_cell_followers().execute(from_cells=sheet2.cells[0:sheet2.sf.size[1]],
                                                       to_cells=sheet2.cells[sheet2.sf.size[1]:], )
        await session.commit()

    # Assert
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet2 = await boot.get_sheet_service().get_sheet_by_uuid(sheet2.sf.id)
        assert sheet2.cells[0].value == 1
        assert sheet2.cells[1].value == 2
        assert sheet2.cells[2].value == 11
        assert sheet2.cells[3].value == 22
        assert sheet2.cells[4].value == 111
        assert sheet2.cells[5].value == 222
