from abc import ABC, abstractmethod

from src.bus.eventbus import Queue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
    repository as sheet_repo,
)
from src.spreadsheet.sheet_info import (
    events as sf_events,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
)


class SheetSubscriber(ABC):
    @abstractmethod
    async def follow_sheet(self, pub: sheet_entity.Sheet):
        raise NotImplemented

    @abstractmethod
    async def unfollow_sheet(self, pub: sheet_entity.Sheet):
        raise NotImplemented

    @abstractmethod
    async def on_rows_appended(self, table: list[list[cell_entity.CellValue]]):
        raise NotImplemented

    @abstractmethod
    async def on_sheet_deleted(self):
        raise NotImplemented


class SheetSelfSubscriber(SheetSubscriber):
    def __init__(self, entity: sheet_entity.Sheet, repo: sheet_repo.SheetRepo, queue: Queue):
        self._entity = entity
        self._events = queue
        self._repo = repo

    async def follow_sheet(self, pub: sheet_entity.Sheet):
        if self._entity.sheet_info.size != (0, 0):
            raise ValueError
        rows = []
        for parent_row in pub.rows:
            child_row = sindex_entity.RowSindex(position=parent_row.position, sheet_info=self._entity.sheet_info)
            rows.append(child_row)
            self._events.append(sindex_events.SindexCreated(entity=child_row))
            self._events.append(sindex_events.SindexSubscribed(pubs=[parent_row], sub=child_row))

        cols = []
        for parent_col in pub.cols:
            child_col = sindex_entity.ColSindex(position=parent_col.position, sheet_info=self._entity.sheet_info)
            cols.append(child_col)
            self._events.append(sindex_events.SindexCreated(entity=child_col))
            self._events.append(sindex_events.SindexSubscribed(pubs=[parent_col], sub=child_col))

        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = i * pub.sheet_info.size[1] + j
                child_cell = cell_entity.Cell(sheet_info=self._entity.sheet_info, row_sindex=row, col_sindex=col,
                                              value=pub.cells[index].value)
                self._events.append(cell_events.CellCreated(entity=child_cell))
                self._events.append(cell_events.CellSubscribed(pubs=[pub.cells[index]], sub=child_cell))

        self._entity.sheet_info.size = pub.sheet_info.size
        self._events.append(
            sf_events.SheetInfoUpdated(old_entity=self._entity.sheet_info, new_entity=self._entity.sheet_info))

    async def unfollow_sheet(self, pub: sheet_entity.Sheet):
        raise NotImplemented

    async def on_rows_appended(self, table: list[list[cell_entity.CellValue]]):
        raise NotImplemented

    async def on_sheet_deleted(self):
        raise NotImplemented
