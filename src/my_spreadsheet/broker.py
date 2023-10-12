from typing import Iterable
from uuid import UUID

from . import domain


class BrokerService:
    def __init__(self):
        self._data: dict[UUID, set[domain.Entity]] = {}

    async def subscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        for pub in pubs:
            if self._data.get(pub.uuid) is None:
                self._data[pub.uuid] = set()
            self._data[pub.uuid].add(sub)

    async def unsubscribe(self, pubs: Iterable[domain.Entity], sub: domain.Entity):
        raise NotImplemented

    async def get_subs(self, pub: domain.Entity) -> set[domain.Entity]:
        if self._data.get(pub.uuid) is None:
            return set()
        return self._data[pub.uuid]
