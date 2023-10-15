from typing import Iterable
from uuid import UUID

from src.spreadsheet import domain
from src.helpers.decorators import singleton


@singleton
class BrokerService:
    def __init__(self):
        self._data: dict[domain.Entity, set[domain.Entity]] = {}

    async def subscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        for pub in pubs:
            if self._data.get(pub) is None:
                self._data[pub] = set()
            self._data[pub].add(sub)

    async def unsubscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        raise NotImplemented

    async def get_subs(self, pub: domain.Entity) -> set[domain.Entity]:
        if self._data.get(pub) is None:
            return set()
        return self._data[pub]

    async def get_pubs(self, sub: domain.Entity) -> set[domain.Entity]:
        result = set(key for key, value in self._data.items() if sub in value)
        return result
