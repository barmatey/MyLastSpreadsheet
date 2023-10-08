from abc import ABC, abstractmethod

from src.bus.eventbus import Queue
from src.spreadsheet.cell.entity import Cell
from . import events


class CellSubscriber(ABC):
    @abstractmethod
    async def follow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def on_cell_updated(self, old: Cell, actual: Cell):
        raise NotImplemented

    @abstractmethod
    async def on_cell_deleted(self, pub: Cell):
        raise NotImplemented


class CellSelfSubscriber(CellSubscriber):
    def __init__(self, entity: Cell):
        self._events = Queue()
        self._entity = entity

    async def follow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        self._events.append(events.CellSubscribed(pubs=pubs, sub=self))
        self._events.append(events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def unfollow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = None
        self._events.append(events.CellUnsubscribed(pubs=pubs, sub=self))
        self._events.append(events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_updated(self, old: Cell, actual: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = actual.value
        self._events.append(events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_deleted(self, pub: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        self._events.append(events.CellUpdated(old_entity=old, new_entity=self._entity))
