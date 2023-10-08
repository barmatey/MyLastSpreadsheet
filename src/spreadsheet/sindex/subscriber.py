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


class SindexSelfSubscriber(SindexSubscriber):
    def __init__(self, entity: Sindex):
        self._events = Queue()
        self._entity = entity

    async def follow_sindexes(self, pubs: list[Sindex]):
        self._events.append(sindex_events.SindexSubscribed(pubs=pubs, sub=self._entity))

    async def unfollow_sindexes(self, pubs: list[Sindex]):
        pass

    async def on_sindex_updated(self, old_value: Sindex, new_value: Sindex):
        pass

    async def on_sindex_deleted(self, pub: Sindex):
        self._events.append(sindex_events.SindexDeleted(entity=self._entity))
        new_sheet = self._entity.sheet_info.model_copy(deep=True)
        new_sheet.size = (new_sheet.size[0] - 1, new_sheet.size[1])
        self._events.append(sheet_events.SheetSizeUpdated(old_entity=self._entity.sheet_info, new_entity=new_sheet))
