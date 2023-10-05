from src.bus.eventbus import Queue
from .domain import CellSubscriber, Cell
from .handlers import CellUpdated, CellSubscribed, CellUnsubscribed


class CellPubsub(CellSubscriber):
    def __init__(self, entity: Cell):
        self._events = Queue()
        self._entity = entity

    def follow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
        self._events.append(CellSubscribed(pubs=pubs, sub=self))

    def unfollow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = None
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
        self._events.append(CellUnsubscribed(pubs=pubs, sub=self))

    def on_cell_updated(self, old: Cell, actual: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = actual.value
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))

    def on_cell_deleted(self, pub: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
