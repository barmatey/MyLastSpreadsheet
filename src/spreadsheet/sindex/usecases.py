from uuid import UUID

from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.repository import SindexRepo, SindexRepoFake
from .entity import Sindex, SindexDirection
from . import events


def create_sindex(sheet: Sheet, position: int, direction: SindexDirection, repo: SindexRepo = SindexRepoFake()):
    sindex = Sindex(sheet=sheet, position=position, direction=direction)
    repo.add(sindex)


def delete_sindex(sindex: Sindex, repo: SindexRepo = SindexRepoFake()):
    repo.remove(sindex)
    Queue().append(events.SindexDeleted(entity=sindex))


def delete_sindexes(sheet: Sheet, row_indexes: list[int], repo: SindexRepo):
    queue = Queue()
    sindexes = repo.get_many(filter_by={"sheet": sheet}, order_by=["position"])
    hashes = {key: 1 for key in row_indexes}

    i = 0
    for sindex in sindexes:
        if hashes.get(sindex.position):
            repo.remove(sindex)
            queue.append(events.SindexDeleted(entity=sindex))
        else:
            new_sindex = sindex.model_copy(deep=True)
            new_sindex.position = i
            repo.update(new_sindex)
            queue.append(events.SindexUpdated(old_entity=sindex, new_entity=new_sindex))
            i += 1
