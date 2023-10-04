from abc import ABC, abstractmethod
from typing import Union, Generic
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.bus.eventbus import Queue
from src.bus.events import Event, Created, Updated, Deleted
from src.spreadsheet.sheet.domain import Sheet

CellValue = Union[int, float, str, bool, datetime, None]


class Cell(BaseModel):
    sheet: Sheet
    value: CellValue = None
    uuid: UUID = Field(default_factory=uuid4)


class CellCreated(Created[Cell]):
    pass


class CellUpdated(Updated[Cell]):
    pass


class CellDeleted(Deleted[Cell]):
    pass


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


class CellFollowed(Event):
    pubs: list[Cell]
    sub: CellSubscriber
    uuid: UUID = Field(default_factory=uuid4)


class CellUnfollowed(Event):
    pubs: list[Cell]
    sub: CellSubscriber
    uuid: UUID = Field(default_factory=uuid4)


class CellPubsub(CellSubscriber):
    def __init__(self, entity: Cell):
        self._events = Queue()
        self._entity = entity
        self._events.append(CellCreated(entity=self._entity))

    def follow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
        self._events.append(CellFollowed(pubs=pubs, sub=self))

    def unfollow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = None
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
        self._events.append(CellUnfollowed(pubs=pubs, sub=self))

    def on_cell_updated(self, old: Cell, actual: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = actual.value
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))

    def on_cell_deleted(self, pub: Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        self._events.append(CellUpdated(old_entity=old, new_entity=self._entity))
