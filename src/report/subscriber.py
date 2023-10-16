from abc import abstractmethod

from src.base.subscriber import Subscriber
from . import domain


class SourceSubscriber(Subscriber):
    @abstractmethod
    async def follow_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def on_wire_appended(self, wire: domain.Wire):
        raise NotImplemented


class PlanItemsSubscriber(Subscriber):
    @abstractmethod
    async def follow_plan_items(self, pub: domain.PlanItems):
        raise NotImplemented
