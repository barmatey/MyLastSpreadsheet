from abc import abstractmethod, ABC
from uuid import UUID

from src.helpers.decorators import singleton
from src.spreadsheet.cell.domain import Cell


class CellRepo(ABC):
    @abstractmethod
    def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID):
        raise NotImplemented

    @abstractmethod
    def update_one(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    def delete_one(self, cell: Cell):
        raise NotImplemented


@singleton
class CellRepoFake(CellRepo):
    def add(self, cell: Cell):
        pass

    def get_one_by_uuid(self, uuid: UUID):
        pass

    def update_one(self, cell: Cell):
        pass

    def delete_one(self, cell: Cell):
        pass
