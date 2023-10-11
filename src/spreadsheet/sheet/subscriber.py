from abc import ABC, abstractmethod

from src.bus.broker import Subscriber
from src.bus.eventbus import Queue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
    repository as sheet_repo,
)
from src.spreadsheet.sheet_info import (
    events as sf_events,
    services as sf_services,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
    services as cell_services,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    services as sindex_services,
)


class SheetSubscriber(Subscriber):
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
