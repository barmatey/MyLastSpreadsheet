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
    ])
    parent_sheet.rows[0].is_freeze = True
    parent_sheet.rows[0].is_readonly = True
    parent_sheet.cols[0].is_freeze = True
    parent_sheet.cols[0].is_readonly = True

    parent_sheet = await create_sheet(parent_sheet)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateCheckerSheet(parent_sheet_id=parent_sheet.sf.id, receiver=boot.get_report_sheet_service())
        actual = await cmd.execute()
        await session.commit()

    assert actual.size == parent_sheet.size
    expected_values = [
        None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1),
        "Revenue", "JackDany", "JackDany", "JackDany",
        "Expenses", "JackDany", "JackDany", "JackDany",
    ]
    for a, expected in zip(actual.cells, expected_values):
        assert a.value == expected
