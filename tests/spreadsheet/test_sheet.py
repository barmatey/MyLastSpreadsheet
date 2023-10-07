import random

import pytest
import pytest_asyncio

import db
from src.bus.eventbus import EventBus
from src.spreadsheet.cell.repository import CellRepoPostgres
from src.spreadsheet.sheet.repository import SheetRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepoPostgres
from src.spreadsheet.sheet import commands as sheet_commands, entity as sheet_entity, usecases as sheet_usecases
from src.spreadsheet.sindex import entity as sindex_entity, usecases as sindex_usecases
from src.spreadsheet.cell import entity as cell_entity, usecases as cell_usecases


@pytest.fixture()
@pytest.mark.asyncio
async def sheet():
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        sindex_repo = SindexRepoPostgres(session)
        cell_repo = CellRepoPostgres(session)

        sheet = sheet_entity.Sheet(size=(11, 5))
        await sheet_repo.add(sheet)

        row_sindexes = []
        for i in range(0, 11):
            row_sindex = sindex_entity.RowSindex(sheet=sheet, position=i)
            await sindex_repo.add(row_sindex)
            row_sindexes.append(row_sindex)

        col_sindexes = []
        for j in range(0, 5):
            col_sindex = sindex_entity.ColSindex(sheet=sheet, position=j)
            await sindex_repo.add(col_sindex)
            col_sindexes.append(col_sindex)

        for row in row_sindexes:
            for col in col_sindexes:
                cell = cell_entity.Cell(sheet=sheet, row_sindex=row, col_sindex=col, value=random.randrange(0, 111))
                await cell_repo.add(cell)

        await session.commit()
        return sheet


@pytest.mark.asyncio
async def test_create_sheet():
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(sheet_repo=sheet_repo)
        sheet = await cmd.execute()
        sheet_from_repo = await sheet_repo.get_one_by_uuid(sheet.uuid)

        assert sheet == sheet_from_repo
        assert sheet.size == (0, 0)


@pytest.mark.asyncio
async def test_delete_rows(sheet: sheet_entity.Sheet):
    sheet = await sheet
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        sindex_repo = SindexRepoPostgres(session)
        cell_repo = CellRepoPostgres(session)

        rows = await sindex_repo.get_sheet_rows(sheet)
        sindexes_to_delete = rows[3:4]

        cells = await cell_repo.get_many_by_sheet_filters(sheet, sindexes_to_delete)

        cmd = sheet_commands.DeleteSindexes(sheet=sheet, sindexes=sindexes_to_delete, sheet_repo=sheet_repo,
                                            sindex_repo=sindex_repo, cell_repo=cell_repo)
        await cmd.execute()
        await session.commit()

    async with db.get_async_session() as session:
        sindex_repo = SindexRepoPostgres(session)
        rows = await sindex_repo.get_sheet_rows(sheet)
        print(rows)
        assert len(rows) == 9

