from uuid import UUID, uuid4

from src.bus.eventbus import Queue
from src.spreadsheet.sheet_info.entity import SheetInfo
from .repository import SindexRepo
from .entity import Sindex, SindexDirection, RowSindex, ColSindex
from . import events


class SindexCreate:
    def __init__(self, row_or_col: SindexDirection, repo: SindexRepo):
        self._repo = repo
        self._entity = RowSindex if row_or_col == "ROW" else ColSindex
        self._sindexes = []

    def create(self, position: int, sheet_info: SheetInfo, uuid: UUID = None):
        if uuid is None:
            uuid = uuid4()
        self._sindexes.append(self._entity(position=position, sheet_info=sheet_info, uuid=uuid))
        return self

    async def save(self):
        await self._repo.add_many(self._sindexes)


async def create_row_sindex(sheet_info: SheetInfo, position: int, repo: SindexRepo) -> Sindex:
    sindex = RowSindex(sheet_info=sheet_info, position=position)
    await repo.add(sindex)
    return sindex


async def delete_sindex(sindex: Sindex, sindex_repo: SindexRepo):
    await sindex_repo.remove_one(sindex)
    queue = Queue()
    queue.append(events.SindexDeleted(entity=sindex))


async def delete_sindexes(sindexes: list[Sindex], repo: SindexRepo):
    await repo.remove_many(sindexes)
    for sindex in sindexes:
        Queue().append(events.SindexDeleted(entity=sindex))


async def reindex_rows(sheet: SheetInfo, repo: SindexRepo):
    rows = await repo.get_sheet_rows(sheet)
    for i, row in enumerate(rows):
        if row.position != i:
            row.position = i
            await repo.update_one(row)


def reindex(sheet: SheetInfo, direction: SindexDirection, repo: SindexRepo):
    sindexes = repo.get_many(filter_by={"sheet": sheet, "direction": direction, }, order_by=["position"])
    for i, sindex in enumerate(sindexes):
        sindex.position = i
        repo.update(sindex)
