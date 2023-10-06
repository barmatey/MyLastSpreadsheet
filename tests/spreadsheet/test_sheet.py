import random

import pytest

from src.bus.eventbus import EventBus
from src.spreadsheet.cell.repository import CellRepoFake
from src.spreadsheet.sheet.repository import SheetRepoFake
from src.spreadsheet.sindex.repository import SindexRepoFake
from src.spreadsheet.sheet import commands as sheet_commands, entity as sheet_entity, usecases as sheet_usecases
from src.spreadsheet.sindex import entity as sindex_entity, usecases as sindex_usecases
from src.spreadsheet.cell import entity as cell_entity, usecases as cell_usecases


@pytest.fixture(scope="function")
def cell_repo():
    repo = CellRepoFake()
    return repo


@pytest.fixture(scope="function")
def sheet_repo():
    repo = SheetRepoFake()
    return repo


@pytest.fixture(scope="function")
def sindex_repo():
    repo = SindexRepoFake()
    return repo


@pytest.fixture(scope='function')
def sheet() -> sheet_entity.Sheet:
    sheet_repository = SheetRepoFake()
    cell_repository = CellRepoFake()
    sindex_repository = SindexRepoFake()
    sheet_repository.clear()
    cell_repository.clear()
    sindex_repository.clear()

    sheet = sheet_entity.Sheet(size=(11, 5))
    sheet_repository.add(sheet)

    for i in range(0, 11):
        row = sindex_entity.Sindex(sheet=sheet, direction="ROW", position=i)
        sindex_repository.add(row)

    for j in range(0, 5):
        col = sindex_entity.Sindex(sheet=sheet, direction="COL", position=j)
        sindex_repository.add(col)

    for i in range(0, 11):
        for j in range(0, 5):
            cell = cell_entity.Cell(sheet=sheet, value=random.randrange(0, 100))
            cell_repository.add(cell)

    return sheet


def test_append_sheet_rows(sheet_repo, cell_repo):
    sheet = sheet_repo.get_one_by_uuid(sheet_usecases.create_sheet())
    assert sheet.size == (0, 0)
    table = [
        [1, 2],
        [3, 4],
    ]
    cmd = sheet_commands.AppendRows(sheet=sheet, table=table)
    cmd.execute()

    sheet = sheet_repo.get_one_by_uuid(sheet.uuid)
    assert sheet.size == (2, 2)

    cells = sorted(cell_repo.get_all(), key=lambda cell: cell.value)
    assert len(cells) == 4
    assert cells[0].value == 1
    assert cells[1].value == 2
    assert cells[2].value == 3
    assert cells[3].value == 4


def test_delete_sheet_rows(sheet_repo, sindex_repo, cell_repo, sheet):
    sindexes = sindex_repo.get_many(filter_by={"sheet": sheet, "direction": "ROW"}, order_by=["position"])
    to_delete = sindexes[2:4]
    cmd = sheet_commands.DeleteSindexes(sheet=sheet, targets=to_delete)
    cmd.execute()

    sheet = sheet_repo.get_one_by_uuid(sheet.uuid)
    assert sheet.size == (9, 5)

    rows = sindex_repo.get_many(filter_by={"sheet": sheet, "direction": "ROW"}, order_by=["position"])
    assert len(rows) == 9
    for i, row in enumerate(rows):
        assert row.position == i

    cells = cell_repo.get_many(filter_by={"sheet": sheet})
    assert len(cells) == 45
