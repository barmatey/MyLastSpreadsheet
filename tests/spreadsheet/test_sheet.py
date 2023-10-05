import pytest

from src.bus.eventbus import EventBus
from src.spreadsheet.sheet import entity as sheet_entity, handlers as sheet_services, repository as sheet_repo
from src.spreadsheet.cell import entity as cell_entity, handlers as cell_services, repository as cell_repo
from src.spreadsheet.sindex import entity as sindex_entity, handlers as sindex_services, repository as sindex_repo


@pytest.fixture
def cell_repo():
    return cell_repo.CellRepoFake()


@pytest.fixture
def sheet_repo():
    return sheet_repo.SheetRepoFake()


def test_append_sheet_rows(sheet_repo: sheet_repo.SheetRepo, cell_repo: cell_repo.CellRepo):
    sheet = sheet_repo.get_one_by_uuid(sheet_services.create_sheet())
    assert sheet.size == (0, 0)
    table = [
        [1, 2],
        [3, 4],
    ]

