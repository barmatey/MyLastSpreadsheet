from abc import ABC, abstractmethod

from .domain import Sindex


class SindexSubscriber(ABC):
    @abstractmethod
    def follow_sindexes(self, pubs: list[Sindex]):
        raise NotImplemented

    @abstractmethod
    def unfollow_sindexes(self, pubs: list[Sindex]):
        raise NotImplemented

    @abstractmethod
    def on_sindex_deleted(self, pub: Sindex):
        raise NotImplemented


