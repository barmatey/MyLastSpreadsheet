from abc import abstractmethod, ABC

from pydantic import BaseModel

from src.base.subscriber import Subscriber
from . import domain


class SourceSubscriber(Subscriber):
    @abstractmethod
    async def follow_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def on_wire_appended(self, wire: domain.Wire):
        raise NotImplemented


class SubscriberFactory(ABC):
    @abstractmethod
    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        raise NotImplemented
