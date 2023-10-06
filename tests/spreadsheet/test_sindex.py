import pytest

from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.repository import SindexRepoFake, SindexRepo
from src.spreadsheet.sindex import usecases as sindex_usecases


@pytest.fixture()
def sindex_repo():
    repo = SindexRepoFake()
    repo.clear()
    return repo


def test_create_sindex(sindex_repo: SindexRepo):
    sheet = Sheet()
    for i in range(0, 11):
        sindex_usecases.create_sindex(sheet, i, "ROW")

    sindexes = sindex_repo.get_all()
    assert len(sindexes) == 11
    for i, sindex in enumerate(sindexes):
        assert sindex.position == i
