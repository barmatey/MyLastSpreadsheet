from abc import ABC, abstractmethod
from src.spreadsheet.cell.entity import CellValue
from .entity import Sheet
from ...bus.eventbus import Queue


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


class SheetSelfSubscriber(SheetSubscriber):
    def __init__(self, entity: Sheet):
        self._entity = entity
        self._queue = Queue()

    def follow_sheet(self, pub: Sheet):
        raise NotImplemented

    def unfollow_sheet(self, pub: Sheet):
        raise NotImplemented

    def on_rows_appended(self, table: list[list[CellValue]]):
        raise NotImplemented

    def on_sheet_deleted(self):
        raise NotImplemented
