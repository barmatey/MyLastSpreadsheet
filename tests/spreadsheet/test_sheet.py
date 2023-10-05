import pytest

from src.bus.eventbus import EventBus
from src.spreadsheet.cell.repository import CellRepoFake, CellRepo
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.pubsub import SheetService
from src.spreadsheet.sheet import handlers
from src.spreadsheet.cell import handlers
from src.spreadsheet.sheet.repository import SheetRepoFake, SheetRepo


@pytest.fixture
def cell_repo():
    return CellRepoFake()


@pytest.fixture
def sheet_repo():
    return SheetRepoFake()


def test_append_sheet_rows(sheet_repo: SheetRepo, cell_repo: CellRepo):
    sheet_pubsub = SheetService(Sheet()).create()
    table = [
        [1, 2],
        [3, 4],
    ]
    sheet_pubsub.append_rows(table)

    bus = EventBus()
    bus.run()
