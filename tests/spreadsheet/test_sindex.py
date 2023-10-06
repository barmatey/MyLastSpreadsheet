import pytest

from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.repository import SindexRepoFake, SindexRepo
from src.spreadsheet.sindex import usecases as sindex_usecases


@pytest.fixture(scope="function")
def sindex_repo():
    repo = SindexRepoFake()
    repo.clear()
    return repo


@pytest.fixture(scope="function")
def load_fake_data():
    sheet = Sheet()
    for i in range(0, 11):
        sindex_usecases.create_sindex(sheet, i, "ROW")


def test_create_sindex(sindex_repo: SindexRepo):
    sheet = Sheet()
    for i in range(0, 11):
        sindex_usecases.create_sindex(sheet, i, "ROW")

    sindexes = sindex_repo.get_all()
    assert len(sindexes) == 11
    for i, sindex in enumerate(sindexes):
        assert sindex.position == i


def test_delete_sindex(sindex_repo: SindexRepo, load_fake_data):
    sindexes = sindex_repo.get_all()
    to_delete = sindexes[0:3]
    for sindex in to_delete:
        sindex_usecases.delete_sindex(sindex)

    sindexes = sindex_repo.get_all()
    assert len(sindexes) == 8
    assert Queue().popleft().entity == to_delete[0]
    assert Queue().popleft().entity == to_delete[1]
    assert Queue().popleft().entity == to_delete[2]
