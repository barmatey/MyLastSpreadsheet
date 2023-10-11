from abc import ABC, abstractmethod

from src.bus.broker import Subscriber
from src.bus.eventbus import Queue
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
)
from src.spreadsheet.sheet import (
    repository as sheet_repo,
)


class CellSubscriber(Subscriber):
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

