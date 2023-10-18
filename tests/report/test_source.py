import random
from datetime import datetime

import pytest
from loguru import logger

import db
from src.report import bootstrap, commands, domain
from src.spreadsheet import commands as sheet_commands


async def create_source():
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSource(title="Hello", receiver=boot.get_source_service())
        source = await cmd.execute()
        await session.commit()
        return source


async def append_wires(source: domain.Source) -> domain.Source:
    wires = [
        domain.Wire(
            sender=i,
            receiver=i,
            amount=random.randrange(0, 111),
            sub1="first" if i % 2 == 0 else "second",
            sub2="no_info",
            date=datetime(2021, i + 1, 5),
            source_info=source.source_info,
        ) for i in range(0, 5)
    ]
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_source_service().append_wires(wires)
        await session.commit()

    source = source.model_copy(deep=True)
    source.wires = wires
    return source


@pytest.mark.asyncio
async def test_create_source():
    source = await create_source()
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        source = await commands.GetSourceById(id=source.source_info.id, receiver=boot.get_source_service()).execute()
        assert source.source_info.title == "Hello"


@pytest.mark.asyncio
async def test_append_wires():
    source = await create_source()
    await append_wires(source)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        source = await commands.GetSourceById(id=source.source_info.id, receiver=boot.get_source_service()).execute()
        assert len(source.wires) == 5


@pytest.mark.asyncio
async def test_create_group():
    source = await create_source()
    source = await append_wires(source)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_group_service()
        expected = await commands.CreateGroup(title="Group", source=source, receiver=receiver,
                                              ccols=['sender', 'sub1']).execute()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_group_service()
        actual = await commands.GetGroupById(id=expected.id, receiver=receiver).execute()
        assert actual.id == expected.id
        for left, right in zip(actual.plan_items.table, expected.plan_items.table):
            assert str(left) == str(right)
        assert actual.plan_items.uniques == expected.plan_items.uniques


@pytest.mark.asyncio
async def test_create_profit_report():
    source = await create_source()
    source = await append_wires(source)
    periods = [domain.Period(from_date=datetime(2021, x, 10), to_date=datetime(2021, x, 15)) for x in range(1, 6)]

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        group = await commands.CreateGroup(title="Group", source=source, receiver=boot.get_group_service(),
                                           ccols=['sender', 'sub1']).execute()
        receiver = boot.get_report_service()
        expected = await commands.CreateReport(source=source, group=group, periods=periods, receiver=receiver).execute()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        report = await commands.GetReportById(id=expected.id, receiver=boot.get_report_service()).execute()
        sheet = await sheet_commands.GetSheetByUuid(uuid=report.sheet_id, receiver=boot.get_sheet_service()).execute()

        logger.debug(f"\n{report}")
        logger.debug(f"\n{sheet.as_table()}")
