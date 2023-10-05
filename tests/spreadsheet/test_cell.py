import pytest

from src.bus.eventbus import Queue, EventBus
from src.spreadsheet.cell.domain import Cell, CellCreated
from src.spreadsheet.cell.pubsub import CellPubsub
from src.spreadsheet.cell.repository import CellRepo, CellRepoFake
from src.spreadsheet.sheet.domain import Sheet


@pytest.fixture
def repo():
    return CellRepoFake()


def test_create_cell_pubsub():
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    CellPubsub(entity=cell)


def test_created_cell_saved_in_repo():
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    CellPubsub(entity=cell)
    bus = EventBus()
    bus.run()


def test_fake_repo(repo: CellRepo):
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    repo.add(cell)
    assert cell.uuid == repo.get_one_by_uuid(cell.uuid).uuid



