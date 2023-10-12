from collections import deque
from typing import Generic, TypeVar
from uuid import UUID, uuid4

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
        self._queue.append(event)