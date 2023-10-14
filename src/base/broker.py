from typing import Iterable
from uuid import UUID

from src.spreadsheet import domain
from src.helpers.decorators import singleton


@singleton
class BrokerService:
    def __init__(self):
        self._data: dict[UUID, set[domain.Entity]] = {}

    async def subscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        for pub in pubs:
            if self._data.get(pub.id) is None:
                self._data[pub.id] = set()
            self._data[pub.id].add(sub)

    async def unsubscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        raise NotImplemented

    async def get_subs(self, pub: domain.Entity) -> set[domain.Entity]:
        if self._data.get(pub.id) is None:
            return set()
        return self._data[pub.id]
