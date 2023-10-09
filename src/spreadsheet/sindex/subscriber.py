from abc import ABC, abstractmethod

from src.bus.eventbus import Queue
from ..sheet import events as sheet_events
from .entity import Sindex
from . import events as sindex_events


class SindexSubscriber(ABC):
    @abstractmethod
    async def follow_sindexes(self, pubs: list[Sindex]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_sindexes(self, pubs: list[Sindex]):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_deleted(self, pub: Sindex):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_updated(self, old_value: Sindex, new_value: Sindex):
        raise NotImplemented


