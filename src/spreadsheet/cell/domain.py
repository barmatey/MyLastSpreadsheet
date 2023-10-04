from abc import ABC, abstractmethod
from typing import Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.bus.eventbus import Event
from src.spreadsheet.sheet.domain import Sheet

CellValue = Union[int, float, str, bool, datetime, None]


class Cell(BaseModel):
    sheet: Sheet
    value: CellValue = None
    uuid: UUID = Field(default_factory=uuid4)


class CellCreated(Event):
    entity: Cell
    uuid: UUID = Field(default_factory=uuid4)


class CellUpdated(Event):
    old_entity: Cell
    new_entity: Cell
    uuid: UUID = Field(default_factory=uuid4)


class CellDeleted(Event):
    entity: Cell
    uuid: UUID = Field(default_factory=uuid4)


class CellSubscriber(ABC):
    @abstractmethod
    def follow(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    def unfollow(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    def on_cell_updated(self, old: Cell, actual: Cell):
        raise NotImplemented

    @abstractmethod
    def on_cell_deleted(self, pub: Cell):
        raise NotImplemented
