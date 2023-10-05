from abc import abstractmethod, ABC
from uuid import UUID

from src.helpers.decorators import singleton
from src.spreadsheet.cell.entity import Cell


class CellRepo(ABC):
    @abstractmethod
    def add(self, cell: Cell):
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

    def add(self, cell: Cell):
        if self._data.get(cell.uuid) is not None:
            raise Exception("already exist")
        self._data[cell.uuid] = cell.model_copy(deep=True)

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
