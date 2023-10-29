from datetime import datetime
import pytz

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
            date=datetime(2021, i + 1, 15, tzinfo=pytz.UTC),
            source_id=source.source_info.id,
        ) for i in range(0, 5)
    ]
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_source_service().append_wires(source.source_info, wires)
        await session.commit()

    source = source.model_copy(deep=True)
    source.wires = wires
    return source


async def create_report(source: domain.Source, interval: domain.Interval) -> domain.Report:
    plan_items = domain.PlanItems(ccols=["sender", "sub1"])
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_report_service()
        report = await commands.CreateReport(title="Hello", source=source, plan_items=plan_items, receiver=receiver,
                                             interval=interval).execute()
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
async def test_create_profit_report():
    source = await create_source()
    source = await append_wires(source)
    periods = [
        domain.Period(from_date=datetime(2021, x, 1, tzinfo=pytz.UTC), to_date=datetime(2021, x, 28, tzinfo=pytz.UTC))
        for x in range(1, 6)
    ]
    interval = domain.Interval(start_date=datetime(2021, 1, 1, tzinfo=pytz.UTC),
                               end_date=datetime(2021, 5, 31, tzinfo=pytz.UTC),
                               freq="1M")
    expected = await create_report(source, interval)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        report = await commands.GetReportById(id=expected.id, receiver=boot.get_report_service()).execute()
        sheet = await sheet_commands.GetSheetByUuid(uuid=report.sheet_id, receiver=boot.get_sheet_service()).execute()

        print()
        df = pd.DataFrame(sheet.to_table())
        print(df.to_string())


@pytest.mark.asyncio
async def test_report_sheet_reacts_on_wire_appended():
    source = await append_wires(await create_source())
    periods = [
        domain.Period(from_date=datetime(2021, x, 1, tzinfo=pytz.UTC), to_date=datetime(2021, x, 28, tzinfo=pytz.UTC))
        for x in range(1, 6)
    ]
    interval = domain.Interval(start_date=datetime(2020, 12, 31, tzinfo=pytz.UTC),
                               end_date=datetime(2021, 5, 31, tzinfo=pytz.UTC),
                               freq="1M")
    report = await create_report(source, interval)

    wire1 = domain.Wire(
        sender=1,
        receiver=1,
        amount=333,
        sub1="AppendedWire1 WTF?",
        sub2="no_info",
        date=datetime(2021, 1, 16,  0, 0, 0, tzinfo=pytz.UTC),
        source_id=source.source_info.id,
    )
    wire2 = domain.Wire(
        sender=11,
        receiver=1,
        amount=777,
        sub1="AppendedWire2",
        sub2="no_info",
        date=datetime(2021, 3, 16, 0, 0, 0, tzinfo=pytz.UTC),
        source_id=source.source_info.id,
    )
    wire3 = domain.Wire(
        sender=2,
        receiver=10,
        sub1="first",
        amount=222,
        date=datetime(2021, 3, 15, 0, 0, 0, tzinfo=pytz.UTC),
        source_id=source.source_info.id,
    )
    wire4 = domain.Wire(
        sender=1,
        receiver=10,
        sub1="second",
        amount=987,
        date=datetime(2021, 5, 15, 0, 0, 0, tzinfo=pytz.UTC),
        source_id=source.source_info.id,
    )
    wire5 = domain.Wire(
        sender=0,
        receiver=10,
        sub1="first",
        amount=987_123,
        date=datetime(2021, 1, 2, 0, 0, 0, tzinfo=pytz.UTC),
        source_id=source.source_info.id,
    )

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        bus = boot.get_event_bus()

        cmd = commands.AppendWires(source_info=source.source_info, wires=[wire1, wire2, wire3,  wire4, wire5],
                                   receiver=boot.get_source_service())
        await cmd.execute()

        cmd = commands.DeleteWires(source_info=source.source_info, wires=[wire1], receiver=boot.get_source_service())
        # await cmd.execute()

        updated = wire3.model_copy(deep=True)
        updated.sender = 99
        cmd = commands.UpdateWires(source_info=source.source_info, wires=[updated], receiver=boot.get_source_service())
        # await cmd.execute()

        await bus.run()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        sheet = await sheet_commands.GetSheetByUuid(uuid=report.sheet_info.id,
                                                    receiver=boot.get_sheet_service()).execute()
        # print("\n", pd.DataFrame(sheet.as_table()).to_string())
