from typing import Iterable

from . import entity
from src.helpers.decorators import singleton


@singleton
class BrokerService:
    def __init__(self):
        self._data: dict[entity.Entity, set[entity.Entity]] = {}

    async def subscribe(self, pubs: Iterable[entity.Entity], sub: entity.Entity):
        for pub in pubs:
            if self._data.get(pub) is None:
                self._data[pub] = set()
            self._data[pub].add(sub)

    async def unsubscribe(self, pubs: Iterable[entity.Entity], sub: entity.Entity):
        raise NotImplemented

    async def get_subs(self, pub: entity.Entity) -> set[entity.Entity]:
        if self._data.get(pub) is None:
            return set()
        return self._data[pub]

    async def get_pubs(self, sub: entity.Entity) -> set[entity.Entity]:
        result = set(key for key, value in self._data.items() if sub in value)
        return result
