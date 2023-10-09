from abc import ABC, abstractmethod

from src.bus.eventbus import Queue
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
    repository as cell_repo,
)


class CellSubscriber(ABC):
    @abstractmethod
    async def follow_cells(self, pubs: list[cell_entity.Cell]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_cells(self, pubs: list[cell_entity.Cell]):
        raise NotImplemented

    @abstractmethod
    async def on_cell_updated(self, old: cell_entity.Cell, actual: cell_entity.Cell):
        raise NotImplemented

    @abstractmethod
    async def on_cell_deleted(self, pub: cell_entity.Cell):
        raise NotImplemented


class CellSelfSubscriber(CellSubscriber):
    def __init__(self, entity: cell_entity.Cell, repo: cell_repo.CellRepo, queue: Queue):
        self._entity = entity
        self._repo = repo
        self._cell_events = queue

    async def follow_cells(self, pubs: list[cell_entity.Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        self._cell_events.append(cell_events.CellSubscribed(pubs=pubs, sub=self))
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def unfollow_cells(self, pubs: list[cell_entity.Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = None
        self._cell_events.append(cell_events.CellUnsubscribed(pubs=pubs, sub=self))
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_updated(self, old: cell_entity.Cell, actual: cell_entity.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = actual.value
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_deleted(self, pub: cell_entity.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))
