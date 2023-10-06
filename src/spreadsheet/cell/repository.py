from abc import abstractmethod, ABC
from uuid import UUID

from src.helpers.decorators import singleton
from src.spreadsheet.cell.entity import Cell


class CellRepo(ABC):
    @abstractmethod
    def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    def get_all(self) -> list[Cell]:
        raise NotImplemented

    @abstractmethod
    def get_many(self, filter_by: dict, order_by: list[str] = None, asc=True):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID) -> Cell:
        raise NotImplemented

    @abstractmethod
    def update_one(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    def delete_one(self, cell: Cell):
        raise NotImplemented


@singleton
class CellRepoFake(CellRepo):
    def __init__(self):
        self._data: dict[UUID, Cell] = {}

    def get_all(self) -> list[Cell]:
        return list(self._data.values())

    def add(self, cell: Cell):
        if self._data.get(cell.uuid) is not None:
            raise Exception("already exist")
        self._data[cell.uuid] = cell.model_copy(deep=True)

    def get_many(self, filter_by: dict, order_by: list[str] = None, asc=True):
        result: list[Cell] = []
        for cell in self._data.values():
            if all([cell.__getattribute__(key) == value for key, value in filter_by.items()]):
                result.append(cell)
        return result

    def get_one_by_uuid(self, uuid: UUID) -> Cell:
        return self._data[uuid].model_copy(deep=True)

    def update_one(self, cell: Cell):
        if self._data.get(cell.uuid) is None:
            raise LookupError
        self._data[cell.uuid] = cell.model_copy(deep=True)

    def delete_one(self, cell: Cell):
        if self._data.get(cell.uuid) is None:
            raise LookupError
        del self._data[cell.uuid]
