import pytest

import db
from src.bus.eventbus import Queue, EventBus
from src.spreadsheet.sindex.repository import SindexRepoPostgres
from src.spreadsheet.sindex.subscriber import SindexSubscriber, SindexSelfSubscriber
from tests.spreadsheet.before import create_sheet
from src.spreadsheet.sindex import usecases as sindex_usecase, entity as sindex_entity, events as sindex_events


@pytest.mark.asyncio
async def test_create_sindex():
    sheet = await create_sheet()
    async with db.get_async_session() as session:
        sindex_repo = SindexRepoPostgres(session)
        actual = await sindex_usecase.create_row_sindex(sheet.sheet_info, 11, sindex_repo)
        expected = sindex_entity.RowSindex(sheet_info=sheet.sheet_info, position=11, uuid=actual.uuid)
        assert actual == expected


@pytest.mark.asyncio
async def test_subscribe_first_sindex_on_second_sindex():
    sheet1 = await create_sheet([[1, 2, 3, ]])
    sheet2 = await create_sheet([[11, 22, 33]])

    parent = sheet1.rows[0]
    child = sheet2.rows[0]

    sub = SindexSelfSubscriber(entity=child)
    await sub.follow_sindexes([parent])

    actual = Queue().popleft()
    assert type(actual) == sindex_events.SindexSubscribed


@pytest.mark.asyncio
async def test_delete_parent_sindex_invoke_cascade_delete_child_sindex():
    sheet1 = await create_sheet([[1, 2, 3, ]])
    sheet2 = await create_sheet([[11, 22, 33]])

    parent = sheet1.rows[0]
    child = sheet2.rows[0]

    sub = SindexSelfSubscriber(entity=child)
    await sub.follow_sindexes([parent])

    async with db.get_async_session() as session:
        sindex_repo = SindexRepoPostgres(session)
        await sindex_usecase.delete_sindex(parent, sindex_repo)
        bus = EventBus()
        # bus.run()
