from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from . import domain

T = TypeVar("T")


class Subscriber(ABC):
    pass


class SindexSubscriber(Subscriber):
    @abstractmethod
    async def follow_sindexes(self, pubs: list[domain.Sindex]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_sindexes(self, pubs: list[domain.Sindex]):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_deleted(self, pub: domain.Sindex):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_updated(self, old_value: domain.Sindex, new_value: domain.Sindex):
        raise NotImplemented


class CellSubscriber(Subscriber):
    @abstractmethod
    async def follow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    @abstractmethod
    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        raise NotImplemented

    @abstractmethod
    async def on_cell_deleted(self, pub: domain.Cell):
        raise NotImplemented


class SheetSubscriber(Subscriber):
    @abstractmethod
    async def follow_sheet(self, pub: domain.Sheet):
        raise NotImplemented

    @abstractmethod
    async def unfollow_sheet(self, pub: domain.Sheet):
        raise NotImplemented

    @abstractmethod
    async def on_rows_appended(self, table: list[list[domain.CellValue]]):
        raise NotImplemented

    @abstractmethod
    async def on_sheet_deleted(self):
        raise NotImplemented


class SubscriberFactory:
    @abstractmethod
    def create_cell_subscriber(self, entity: domain.Cell, **kwargs) -> CellSubscriber:
        raise NotImplemented

    @abstractmethod
    def create_sindex_subscriber(self, entity: domain.Sindex, **kwargs) -> SindexSubscriber:
        raise NotImplemented

    @abstractmethod
    def create_sheet_subscriber(self, entity: domain.Sheet, **kwargs) -> SheetSubscriber:
        raise NotImplemented
