from collections import deque
from typing import Generic, TypeVar, Callable
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

T = TypeVar("T")


class Event(BaseModel):
    key: str
    id: UUID


class Updated(Event, Generic[T]):
    old_entity: T
    actual_entity: T
    id: UUID = Field(default_factory=uuid4)


class Deleted(Event, Generic[T]):
    entity: T
    id: UUID = Field(default_factory=uuid4)


class Queue:
    def __init__(self):
        self._queue: deque = deque()

    def append(self, event: Event):
        logger.debug(f"APPEND: {event.key}")
        self._queue.append(event)

    def popleft(self) -> Event:
        event = self._queue.popleft()
        logger.debug(f"EXTRACT: {event}")
        return event

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
            handler = self._handlers[event.key]
            await handler(event)
