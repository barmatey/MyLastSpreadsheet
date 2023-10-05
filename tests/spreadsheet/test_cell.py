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


def test_fake_repo(repo: CellRepo):
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    repo.add(cell)
    assert cell.uuid == repo.get_one_by_uuid(cell.uuid).uuid


def test_subscribed_cell_changes_value_when_subscribing(repo: CellRepo):
    sheet = Sheet()
    parent_cell = CellPubsub(entity=Cell(sheet=sheet, value=1)).create()
    child_cell = CellPubsub(entity=Cell(sheet=sheet)).create()
    child_cell.follow_cells([parent_cell.entity])

    bus = EventBus()
    bus.run()

    parent_cell = repo.get_one_by_uuid(parent_cell.entity.uuid)
    child_cell = repo.get_one_by_uuid(child_cell.entity.uuid)
    assert parent_cell.value == child_cell.value
