from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.repository import SindexRepo, SindexRowRepoFake
from . import events


def delete_rows(sheet: Sheet, row_indexes: list[int], repo: SindexRepo = SindexRowRepoFake):
    sindexes = repo.get_many(filter_by={"sheet": sheet}, order_by=["position"])
    to_delete = []
    to_update = []

