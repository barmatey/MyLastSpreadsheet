from abc import ABC, abstractmethod

from src.spreadsheet.cell.domain import Cell, CellPubsub, CellSubscriber


class CellRepo(ABC):
    def add(self, data: Cell):
        raise NotImplemented

    def get_subscribers(self, pub: Cell) -> CellSubscriber:
        raise NotImplemented
