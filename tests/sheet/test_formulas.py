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
        [1, 2, 3],
        [4, 5, 6],
    ])
    sheet = await create_sheet(sheet)
    target_cell = sheet.cells[5]
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateFormula(
            parents=sheet.cells[0:3],
            target=target_cell,
            formula_key="SUM",
            receiver=boot.get_sheet_service(),
        )
        formula = await cmd.execute()
        assert formula.value == 6
        await session.commit()

    async with db.get_async_session() as session:
        cell = sheet.cells[0].model_copy()
        cell.value = 1000
        boot = bootstrap.Bootstrap(session)
        cmd = commands.UpdateCells(
            data=[cell],
            receiver=boot.get_sheet_service(),
        )
        await cmd.execute()

        await boot.get_event_bus().run()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        target_cell = await boot.get_sheet_service().cell_service.get_by_id(target_cell.id)
        assert target_cell.value == 1005
