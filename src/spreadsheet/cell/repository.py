from abc import ABC, abstractmethod

from src.spreadsheet.cell.domain import Cell


class CellRepo(ABC):
    def add(self, data: Cell):
        raise NotImplemented
