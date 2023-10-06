from abc import ABC, abstractmethod
from uuid import UUID

from src.helpers.decorators import singleton
from src.spreadsheet.sindex.entity import Sindex


class SindexRepo(ABC):
    @abstractmethod
    def add(self, sindex: Sindex):
        raise NotImplemented

    @abstractmethod
    def get_many(self, filter_by: dict, order_by: list, asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID) -> Sindex:
        raise NotImplemented

    @abstractmethod
    def get_many_by_positions(self, sheet_uuid: UUID, positions: list[int],
                              order_by: list[str] = None, asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    def remove_many_by_position(self, sheet_uuid: UUID, positions: list[int]):
        raise NotImplemented

    @abstractmethod
    def remove_many_by_uuid(self, uuids: list[UUID]):
        raise NotImplemented


class SindexRepoFake(SindexRepo):
    def __init__(self):
        self._data: dict[UUID, Sindex] = {}

    def add(self, sindex: Sindex):
        if self._data.get(sindex.uuid) is not None:
            raise Exception("already exist")
        self._data[sindex.uuid] = sindex.model_copy(deep=True)

    def get_many(self, filter_by: dict, order_by: list, asc=True) -> list[Sindex]:
        result: list[Sindex] = []
        for sindex in self._data.values():
            if all([sindex.__getattribute__(key) == value for key, value in filter_by.items()]):
                result.append(sindex)
        if len(order_by) != 1 or order_by[0] != "position":
            raise Exception

        result.sort(key=lambda x: x.position)
        return result

    def get_one_by_uuid(self, uuid: UUID) -> Sindex:
        return self._data[uuid].model_copy(deep=True)

    def get_many_by_positions(self, sheet_uuid: UUID, positions: list[int], order_by: list[str] = None, asc=True):
        result: list[Sindex] = []
        for sindex in self._data.values():
            if all([sindex.sheet.uuid == sheet_uuid, sindex.position in positions]):
                result.append(sindex)
        return result

    def remove_many_by_position(self, sheet_uuid: UUID, positions: list[int]):
        to_remove: list[UUID] = []
        for uuid, sindex in self._data.items():
            if all([sindex.sheet.uuid == sheet_uuid, sindex.position in positions]):
                to_remove.append(uuid)
        for uuid in to_remove:
            del self._data[uuid]

    def remove_many_by_uuid(self, uuids: list[UUID]):
        for uuid in uuids:
            del self._data[uuid]


@singleton
class SindexRowRepoFake(SindexRepoFake):
    pass


@singleton
class SindexColRepoFake(SindexRepoFake):
    pass
