from abc import abstractmethod, ABC
from uuid import UUID

from src.bus.eventbus import Queue
from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed
from src.spreadsheet.cell.domain import Cell, CellSubscriber


class CellRepo(ABC):
    @abstractmethod
    def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID):
        raise NotImplemented


class CellCreated(Created[Cell]):
    def handle(self):
        raise NotImplemented


class CellUpdated(Updated[Cell]):
    def handle(self):
        raise NotImplemented


class CellDeleted(Deleted[Cell]):
    def handle(self):
        raise NotImplemented


class CellSubscribed(Subscribed):
    def handle(self):
        raise NotImplemented


class CellUnsubscribed(Unsubscribed):
    def handle(self):
        raise NotImplemented


