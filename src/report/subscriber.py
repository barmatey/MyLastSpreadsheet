from abc import abstractmethod, ABC

from pydantic import BaseModel

from src.base.subscriber import Subscriber
from . import domain


class SourceSubscriber(Subscriber):
    @abstractmethod
    async def follow_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def on_wires_appended(self, wires: list[domain.Wire]):
        raise NotImplemented


class GroupSubscriber(Subscriber):
    @abstractmethod
    async def follow_group(self, group: domain.Group):
        raise NotImplemented

    @abstractmethod
    async def on_rows_inserted(self, data: list[tuple[int, list[domain.CellValue]]]):
        raise NotImplemented


class SubscriberFactory(ABC):
    @abstractmethod
    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        raise NotImplemented

    @abstractmethod
    def create_group_subscriber(self, entity: BaseModel) -> GroupSubscriber:
        raise NotImplemented
