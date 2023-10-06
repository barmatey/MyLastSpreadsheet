from uuid import UUID

from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from .repository import SindexRepo, SindexRepoFake
from .entity import Sindex, SindexDirection
from . import events


def create_sindex(sheet: Sheet, position: int, direction: SindexDirection, repo: SindexRepo = SindexRepoFake()):
    sindex = Sindex(sheet=sheet, position=position, direction=direction)
    repo.add(sindex)


def delete_sindex(sindex: Sindex, sindex_repo: SindexRepo = SindexRepoFake()):
    sindex_repo.remove(sindex)
    queue = Queue()
    queue.append(events.SindexDeleted(entity=sindex))


def reindex(sheet: Sheet, direction: SindexDirection, repo: SindexRepo = SindexRepoFake()):
    sindexes = repo.get_many(filter_by={"sheet": sheet, "direction": direction, }, order_by=["position"])
    for i, sindex in enumerate(sindexes):
        sindex.position = i
        repo.update(sindex)
