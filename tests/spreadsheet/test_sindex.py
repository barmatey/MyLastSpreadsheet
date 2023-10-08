import pytest

import db
from src.spreadsheet.sindex.repository import SindexRepoPostgres
from tests.spreadsheet.before import create_sheet
from src.spreadsheet.sindex import usecases as sindex_usecase, entity as sindex_entity


@pytest.mark.asyncio
async def test_create_sindex():
    sheet = await create_sheet()
    async with db.get_async_session() as session:
        sindex_repo = SindexRepoPostgres(session)
        actual = await sindex_usecase.create_row_sindex(sheet.sheet_info, 11, sindex_repo)
        expected = sindex_entity.RowSindex(sheet_info=sheet.sheet_info, position=11, uuid=actual.uuid)
        assert actual == expected
