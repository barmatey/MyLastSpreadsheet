from typing import TypeVar, Generic
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)


T = TypeVar("T")


class Created(Event, Generic[T]):
    entity: T
    uuid: UUID = Field(default_factory=uuid4)


class Updated(Event, Generic[T]):
    old_entity: T
    new_entity: T
    uuid: UUID = Field(default_factory=uuid4)


class Deleted(Event, Generic[T]):
    entity: T
    uuid: UUID = Field(default_factory=uuid4)


P = TypeVar("P")
S = TypeVar("S")


class Subscribed(Event, Generic[P, S]):
    pubs: list[P]
    sub: S
    uuid: UUID = Field(default_factory=uuid4)


class Unsubscribed(Event, Generic[P, S]):
    pubs: list[P]
    sub: S
    uuid: UUID = Field(default_factory=uuid4)
