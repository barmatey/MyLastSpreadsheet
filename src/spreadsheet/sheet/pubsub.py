from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from pydantic import Field

from src.bus.eventbus import Queue
from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed, Event

from ..cell.domain import CellValue, Cell
from ..cell.pubsub import CellService
from ..sheet.entity import Sheet


class SheetCreated(Created[Sheet]):
    pass


class SheetSizeUpdated(Updated[Sheet]):
    pass


class SheetDeleted(Deleted[Sheet]):
    pass


class SheetSubscribed(Subscribed):
    pass


class SheetUnsubscribed(Unsubscribed):
    pass


class SheetRowsAppended(Event):
    table: list[list[CellValue]]
    uuid: UUID = Field(default_factory=uuid4)


class SheetSubscriber(ABC):
    @abstractmethod
    def follow_sheet(self, pub: Sheet):
        raise NotImplemented

    @abstractmethod
    def unfollow_sheet(self, pub: Sheet):
        raise NotImplemented

    @abstractmethod
    def on_rows_appended(self, table: list[list[CellValue]]):
        raise NotImplemented

    @abstractmethod
    def on_sheet_deleted(self):
        raise NotImplemented


class SheetService(SheetSubscriber):
    def __init__(self, entity: Sheet):
        self._events = Queue()
        self._entity = entity

    @property
    def entity(self):
        return self._entity.model_copy(deep=True)

    def create(self):
        self._events.append(SheetCreated(entity=self._entity))
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
        self._events.append(SheetSizeUpdated(old_entity=old, new_entity=self._entity))
        # self._events.append(SheetRowsAppended(table=table))

    def follow_sheet(self, pub: Sheet):
        if self._entity.size != (0, 0):
            raise Exception

    def unfollow_sheet(self, pub: Sheet):
        pass

    def on_rows_appended(self, table: list[list[CellValue]]):
        pass

    def on_sheet_deleted(self):
        pass
