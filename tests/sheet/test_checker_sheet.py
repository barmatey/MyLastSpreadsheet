from datetime import datetime

import pytest

import db
from src.sheet import bootstrap, commands, domain


@pytest.mark.asyncio
async def create_sheet(sheet: domain.Sheet):
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSheet(data=sheet, receiver=boot.get_sheet_service())
        result = await cmd.execute()
        await session.commit()
        return result


@pytest.mark.asyncio
async def test_create_report_checker_sheet():
    parent_sheet = domain.Sheet.from_table([
        [None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)],
        ["Revenue", 100, 200, 300],
        ["Expenses", 50, 75, 175],
    ], freeze_rows=1, freeze_cols=1)

    parent_sheet = await create_sheet(parent_sheet)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateCheckerSheet(parent_sheet_id=parent_sheet.sf.id, receiver=boot.get_report_sheet_service())
        actual = await cmd.execute()
        await session.commit()

    assert actual.size == (parent_sheet.size[0] * 2 - 1, parent_sheet.size[1])
    expected_values = [
        None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1),
        "Revenue", 0, 0, 0,
        "", -100, -200, -300,
        "Expenses", 0, 0, 0,
        "", -50, -75, -175,
    ]
    actual_values = [x.value for x in actual.cells]
    assert str(actual_values) == str(expected_values)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        broker = boot.get_broker()
        for parent_row in parent_sheet.rows:
            subs = await broker.get_subs(parent_row)
            if parent_row.is_freeze:
                assert len(subs) == 1
            else:
                assert len(subs) == 2
        for parent_col in parent_sheet.cols:
            subs = await broker.get_subs(parent_col)
            assert len(subs) == 1

