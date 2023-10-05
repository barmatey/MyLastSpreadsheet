from abc import ABC, abstractmethod
from typing import Union, Generic, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.bus.events import Event, Created, Updated, Deleted, Subscribed, Unsubscribed
from src.spreadsheet.sheet.domain import Sheet

CellValue = Union[int, float, str, bool, datetime, None]


class Cell(BaseModel):
    sheet: Sheet
    value: CellValue = None
    uuid: UUID = Field(default_factory=uuid4)


class CellSubscriber(ABC):
    @abstractmethod
    def follow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    def unfollow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    def on_cell_updated(self, old: Cell, actual: Cell):
        raise NotImplemented

    @abstractmethod
    def on_cell_deleted(self, pub: Cell):
        raise NotImplemented


class CellCreated(Created[Cell]):
    pass


class CellUpdated(Updated[Cell]):
    pass


class CellDeleted(Deleted[Cell]):
    pass


class CellSubscribed(Subscribed):
    pass


class CellUnsubscribed(Unsubscribed):
    pass
