import pytest

import db
from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import SheetRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepo, SindexRepoPostgres
from src.spreadsheet.sindex import usecases as sindex_usecases


@pytest.fixture
async def sheet():
    async with db.get_async_session() as session:
        sheet_repo = SheetRepoPostgres(session)
        sheet = Sheet()
