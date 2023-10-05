from abc import ABC, abstractmethod

from src.spreadsheet.cell.entity import Cell


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

