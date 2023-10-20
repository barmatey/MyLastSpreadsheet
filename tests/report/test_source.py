import random
from datetime import datetime

import pandas as pd
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
            amount=111,
            sub1="first" if i % 2 == 0 else "second",
            sub2="no_info",
            date=datetime(2021, i + 1, 15),
            source_info=source.source_info,
        ) for i in range(0, 5)
    ]
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_source_service().append_wires(source.source_info, wires)
        await session.commit()

    source = source.model_copy(deep=True)
    source.wires = wires
    return source


async def create_group(source: domain.Source) -> domain.Group:
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_group_service()
        group = await commands.CreateGroup(title="Group", source=source, receiver=receiver,
                                           ccols=['sender', 'sub1']).execute()
        await session.commit()
        return group


async def create_report(source: domain.Source, group: domain.Group, periods: list[domain.Period]) -> domain.Report:
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_report_service()
        report = await commands.CreateReport(source=source, group=group, periods=periods, receiver=receiver).execute()
        await session.commit()
        return report


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
    expected = await create_group(source)

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
    group = await create_group(source)
    periods = [domain.Period(from_date=datetime(2021, x, 1), to_date=datetime(2021, x, 28)) for x in range(1, 6)]
    expected = await create_report(source, group, periods)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        report = await commands.GetReportById(id=expected.id, receiver=boot.get_report_service()).execute()
        sheet = await sheet_commands.GetSheetByUuid(uuid=report.sheet_id, receiver=boot.get_sheet_service()).execute()

        print()
        df = pd.DataFrame(sheet.as_table())
        print(df.to_string())


@pytest.mark.asyncio
async def test_report_sheet_reacts_on_wire_appended():
    source = await append_wires(await create_source())
    group = await create_group(source)
    periods = [domain.Period(from_date=datetime(2021, x, 1), to_date=datetime(2021, x, 28)) for x in range(1, 6)]
    report = await create_report(source, group, periods)

    wire1 = domain.Wire(
        sender=1,
        receiver=1,
        amount=333,
        sub1="AppendedWire1",
        sub2="no_info",
        date=datetime(2021, 1, 16),
        source_info=source.source_info,
    )
    wire2 = domain.Wire(
        sender=11,
        receiver=1,
        amount=777,
        sub1="AppendedWire2",
        sub2="no_info",
        date=datetime(2021, 3, 16),
        source_info=source.source_info,
    )

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.AppendWires(source_info=source.source_info, wires=[wire1, wire2], receiver=boot.get_source_service())
        await cmd.execute()
        bus = boot.get_event_bus()
        await bus.run()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet = await sheet_commands.GetSheetByUuid(uuid=report.sheet_id, receiver=boot.get_sheet_service()).execute()
        group = await commands.GetGroupById(id=group.id, receiver=boot.get_group_service()).execute()
        print("\n", pd.DataFrame(sheet.as_table()).to_string())
