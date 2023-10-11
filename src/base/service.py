from abc import ABC, abstractmethod
from collections import deque
from typing import TypeVar, Generic, Iterable, Callable, Type
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from src.core import OrderBy

T = TypeVar("T")


class Event(BaseModel):
    key: str
    uuid: UUID = Field(default_factory=uuid4)


class Updated(Event, Generic[T]):
    old: T
    actual: T
    uuid: UUID = Field(default_factory=uuid4)


class ManyUpdated(Event, Generic[T]):
    old: list[T]
    actual: list[T]
    uuid: UUID = Field(default_factory=uuid4)


class ManyDeleted(Event, Generic[T]):
    entities: list[T]
    uuid: UUID = Field(default_factory=uuid4)


class Queue:
    def __init__(self):
        self._queue: deque[Event] = deque()

    def append(self, event: Event):
        self._queue.append(event)

    def popleft(self):
        return self._queue.popleft()

    @property
    def empty(self):
        return len(self._queue) == 0


class EventBus:
    def __init__(self, queue: Queue):
        self._queue = queue
        self._handlers: dict[str, Callable] = {}

    def register(self, key: str, handler: Callable):
        self._handlers[key] = handler

    async def run(self):
        while not self._queue.empty:
            event = self._queue.popleft()
            logger.debug(f"Extracted: {event}")
            handler = self._handlers[event.key]
            await handler(event)


class Entity(BaseModel):
    uuid: UUID


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add_many(self, data: list[T]):
        raise NotImplemented

    @abstractmethod
    async def get_many_by_uuid(self, uuids: list[UUID], order_by: OrderBy) -> list[T]:
        raise NotImplemented

    @abstractmethod
    async def update_many(self, data: list[T]):
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, data: list[T]):
        raise NotImplemented


class Service(Generic[T]):
    def __init__(self, repo: Repository[T], queue: Queue):
        self._repo = repo
        self._queue = queue

    async def create_many(self, data: list[T]):
        await self._repo.add_many(data)

    async def update_many(self, data: list[T], old_values: list[T] = None):
        await self._repo.update_many(data)

    async def delete_many(self, data: list[T]):
        await self._repo.remove_many(data)


class Broker:
    def __init__(self):
        self._data: dict[Entity, set[Entity]] = {}

    def subscribe(self, pubs: Iterable[Entity], sub: Entity):
        for pub in pubs:
            if self._data.get(pub) is None:
                self._data[pub] = set()
            self._data[pub].add(sub)

    def get_subs(self, pub: Entity) -> set[Entity]:
        raise NotImplemented


class Subscriber(Generic[T]):
    def __init__(self, entity: T, service: Service[T], broker: Broker):
        self._entity = entity
        self._service = service
        self._broker = broker

    @property
    def entity(self) -> T:
        return self._entity


class SubscriberFactory:
    def __init__(self, producers: dict[Type[T], Type[Subscriber[T]]]):
        self._producers = producers

    def create_subscriber(self, entity: T, **kwargs) -> Subscriber[T]:
        producer = self._producers[type(entity)]
        return producer(entity, **kwargs)


"""Realisations"""


class RepoPostgres(Repository):
    async def add_many(self, data: list[T]):
        pass

    async def get_many_by_uuid(self, uuids: list[UUID], order_by: OrderBy) -> list[T]:
        pass

    async def update_many(self, data: list[T]):
        pass

    async def remove_many(self, data: list[T]):
        pass
