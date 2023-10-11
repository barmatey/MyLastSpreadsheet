from abc import ABC, abstractmethod

from loguru import logger

from src.bus.broker import Subscriber
from src.bus.eventbus import Queue
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_queue,
    repository as sindex_repo,
)
from src.spreadsheet.sheet_info import (
    events as sf_queue,
)
from src.spreadsheet.sheet import (
    services as sheet_services,
    repository as sheet_repo,
)


class SindexSubscriber(Subscriber):
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

