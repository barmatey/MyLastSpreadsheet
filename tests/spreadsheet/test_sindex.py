import pytest

import db
from src.bus.eventbus import Queue
from src.spreadsheet.sheet_info.entity import SheetMeta
from src.spreadsheet.sheet_info.repository import SheetInfoRepoPostgres
from src.spreadsheet.sindex.repository import SindexRepo, SindexRepoPostgres
from src.spreadsheet.sindex import usecases as sindex_usecases


@pytest.fixture
async def sheet():
    async with db.get_async_session() as session:
        sheet_repo = SheetInfoRepoPostgres(session)
        sheet = SheetMeta()
