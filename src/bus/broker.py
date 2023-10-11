from abc import ABC
from typing import TypeVar, Any
from uuid import UUID

from src.helpers.decorators import singleton

Publisher = TypeVar("Publisher")


class Subscriber(ABC):
    @property
    def entity(self):
        raise NotImplemented


@singleton
class Broker:
    def __init__(self):
        self._subscribers: dict[Publisher, set[Subscriber]] = {}
        self._services: dict[Subscriber, Any] = {}

    def subscribe(self, pub: Publisher, sub: Subscriber):
        if self._subscribers.get(pub) is None:
            self._subscribers[pub] = set()
        self._subscribers[pub].add(sub.entity)
        self._services[sub.entity] = type(sub)

    def subscribe_to_many(self, pubs: list[Publisher], sub: Subscriber):
        for pub in pubs:
            self.subscribe(pub, sub)

    def unsubscribe(self, pub: Publisher, sub: Subscriber):
        self._subscribers[pub].remove(sub)
        if len(self._subscribers[pub]) == 0:
            del self._subscribers[pub]

    def unsubscribe_from_many(self, pubs: list[Publisher], sub: Subscriber):
        for pub in pubs:
            self.unsubscribe(pub, sub)

    def get_subscribers(self, pub, repo,  queue) -> set:
        subs = self._subscribers.get(pub)
        if subs is None:
            subs = set()
        subs = set(self._services[sub](sub, repo, queue) for sub in subs)
        return subs
