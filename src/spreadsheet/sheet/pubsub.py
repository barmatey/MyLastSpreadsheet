from src.bus.eventbus import Queue
from .subscriber import SheetSubscriber

from ..cell.entity import CellValue, Cell
from ..cell.pubsub import CellService
from ..sheet.entity import Sheet
from . import events


class SheetService(SheetSubscriber):
    def __init__(self, entity: Sheet):
        self._events = Queue()
        self._entity = entity

    @property
    def entity(self):
        return self._entity.model_copy(deep=True)

    def create(self):
        self._events.append(events.SheetCreated(entity=self._entity))
        return self

    def append_rows(self, table: list[CellValue] | list[list[CellValue]]):
        old = self._entity.model_copy(deep=True)
        if len(table) == 0:
            raise Exception
        if not isinstance(table[0], list):
            table = [table]
        if self._entity.size == (0, 0):
            self._entity.size = (0, len(table[0]))

        for i, row in enumerate(table):
            if len(row) != self._entity.size[1]:
                raise Exception
            for j, cell_value in enumerate(row):
                CellService(Cell(sheet=self._entity, value=cell_value)).create()

        self._entity.size = (self._entity.size[0] + len(table), self._entity.size[1])
        self._events.append(events.SheetSizeUpdated(old_entity=old, new_entity=self._entity))
        # self._events.append(SheetRowsAppended(table=table))

    def follow_sheet(self, pub: Sheet):
        raise NotImplemented

    def unfollow_sheet(self, pub: Sheet):
        raise NotImplemented

    def on_rows_appended(self, table: list[list[CellValue]]):
        raise NotImplemented

    def on_sheet_deleted(self):
        raise NotImplemented
