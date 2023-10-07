from abc import ABC, abstractmethod

from .entity import Sindex


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
    async def follow_sindexes(self, pubs: list[Sindex]):
        pass

    async def unfollow_sindexes(self, pubs: list[Sindex]):
        pass

    async def on_sindex_updated(self, old_value: Sindex, new_value: Sindex):
        pass

    async def on_sindex_deleted(self, pub: Sindex):
        pass
