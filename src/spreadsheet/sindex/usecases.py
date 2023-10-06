from uuid import UUID

from src.bus.eventbus import Queue
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sindex.repository import SindexRepo, SindexRepoFake
from .entity import Sindex, SindexDirection
from . import events


def create_sindex(sheet: Sheet, position: int, direction: SindexDirection, repo: SindexRepo = SindexRepoFake()):
    sindex = Sindex(sheet=sheet, position=position, direction=direction)
    repo.add(sindex)


def delete_sindex(sindex: Sindex, sindex_repo: SindexRepo = SindexRepoFake()):
    sindex_repo.remove(sindex)
    queue = Queue()
    queue.append(events.SindexDeleted(entity=sindex))
