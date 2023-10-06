import pytest

from src.bus.eventbus import EventBus
from src.spreadsheet.cell.repository import CellRepoFake
from src.spreadsheet.sheet.commands import AppendRows
from src.spreadsheet.sheet.repository import SheetRepoFake
from src.spreadsheet.sheet import entity as sheet_entity, usecases as sheet_usecases
from src.spreadsheet.cell import entity as cell_entity, handlers as cell_services
from src.spreadsheet.sindex import entity as sindex_entity, handlers as sindex_services


@pytest.fixture
def cell_repo():
    return CellRepoFake()


@pytest.fixture
def sheet_repo():
    return SheetRepoFake()


def test_temp():
    assert 1 == 1


def test_append_sheet_rows(sheet_repo, cell_repo):
    sheet = sheet_repo.get_one_by_uuid(sheet_usecases.create_sheet())
    assert sheet.size == (0, 0)
    table = [
        [1, 2],
        [3, 4],
    ]
    cmd = AppendRows(sheet=sheet, table=table)
    cmd.execute()

    sheet = sheet_repo.get_one_by_uuid(sheet.uuid)
    assert sheet.size == (2, 2)

    cells = sorted(cell_repo.get_all(), key=lambda cell: cell.value)
    assert len(cells) == 4
    assert cells[0].value == 1
    assert cells[1].value == 2
    assert cells[2].value == 3
    assert cells[3].value == 4
