import pytest

import db
from src.sheet import domain, bootstrap, commands


@pytest.mark.asyncio
async def create_sheet(sheet: domain.Sheet):
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSheet(data=sheet, receiver=boot.get_sheet_service())
        result = await cmd.execute()
        await session.commit()
        return result


@pytest.mark.asyncio
async def test_formula_cells_react_on_parent_changes():
    sheet = domain.Sheet.from_table([
        [0, 0, 0],
        [0, 0, 0],
    ])
    sheet = await create_sheet(sheet)
