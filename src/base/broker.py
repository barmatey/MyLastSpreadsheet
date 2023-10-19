from typing import Iterable

from pydantic import BaseModel

from src.helpers.decorators import singleton


@singleton
class BrokerService:
    def __init__(self):
        self._data: dict[BaseModel, set[BaseModel]] = {}

    async def subscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        for pub in pubs:
            if self._data.get(pub) is None:
                self._data[pub] = set()
            self._data[pub].add(sub)

    async def unsubscribe(self, pubs: Iterable[BaseModel], sub: BaseModel):
        raise NotImplemented

    async def get_subs(self, pub: BaseModel) -> set[BaseModel]:
        if self._data.get(pub) is None:
            return set()
        return self._data[pub]

    async def get_pubs(self, sub: BaseModel) -> set[BaseModel]:
        result = set(key for key, value in self._data.items() if sub in value)
        return result
