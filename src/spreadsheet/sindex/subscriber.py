from abc import ABC, abstractmethod

from src.bus.eventbus import Queue
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    repository as sindex_repo,
)
from src.spreadsheet.sheet_info import (
    events as sf_events,
)
from src.spreadsheet.sheet import (
    services as sheet_services,
    repository as sheet_repo,
)


class SindexSubscriber(ABC):
    @abstractmethod
    async def follow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_deleted(self, pub: sindex_entity.Sindex):
        raise NotImplemented

    @abstractmethod
    async def on_sindex_updated(self, old_value: sindex_entity.Sindex, new_value: sindex_entity.Sindex):
        raise NotImplemented


class SindexSelfSubscriber(SindexSubscriber):
    def __init__(self, entity: sindex_entity.Sindex, repo: sheet_repo.SheetRepo, queue: Queue):
        self._events = queue
        self._entity = entity
        self._repo = repo

    async def follow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        pass

    async def unfollow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        pass

    async def on_sindex_updated(self, old_value: sindex_entity.Sindex, new_value: sindex_entity.Sindex):
        pass

    async def on_sindex_deleted(self, pub: sindex_entity.Sindex):
        self._events.append(sindex_events.SindexDeleted(entity=self._entity))
        new_sheet = self._entity.sheet_info.model_copy(deep=True)
        new_sheet.size = (new_sheet.size[0] - 1, new_sheet.size[1])
        self._events.append(sf_events.SheetInfoUpdated(old_entity=self._entity.sheet_info, new_entity=new_sheet))
