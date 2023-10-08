import random

import pytest
import pytest_asyncio

import db
from src.core import OrderBy
from src.spreadsheet.cell.repository import CellRepoPostgres
from src.spreadsheet.sheet_info.repository import SheetInfoRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepoPostgres
from src.spreadsheet.sheet import (entity as sheet_entity, commands as sheet_commands)


@pytest.mark.asyncio
async def test_create_sheet():
    async with db.get_async_session() as session:
        sm_repo = SheetInfoRepoPostgres(session)
        sindex_repo = SindexRepoPostgres(session)
        cell_repo = CellRepoPostgres(session)
        cmd = sheet_commands.CreateSheet(
            table=[[0, 1], [2, 3], [4, 5]],
            sheet_meta_repo=sm_repo,
            sindex_repo=sindex_repo,
            cell_repo=cell_repo,
        )
        sheet = await cmd.execute()

        assert sheet.sheet_info.size == (3, 2)
        for i in range(0, 6):
            assert sheet.cells[i].value == i
