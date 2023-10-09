from typing import TypeVar, Generic, Mapping
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def __str__(self):
        return f"{self.__class__.__name__}"


T = TypeVar("T")


class Created(Event, Generic[T]):
    entity: T
    uuid: UUID = Field(default_factory=uuid4)


class Requested(Event):
    uuid: UUID


class Updated(Event, Generic[T]):
    old_entity: T
    new_entity: T
    uuid: UUID = Field(default_factory=uuid4)


class Deleted(Event, Generic[T]):
    entity: T
    uuid: UUID = Field(default_factory=uuid4)


P = TypeVar("P")
S = TypeVar("S")


class Subscribed(Event):
    pubs: list[P]
    sub: S
    uuid: UUID = Field(default_factory=uuid4)


class Unsubscribed(Event):
    pubs: list[P]
    sub: S
    uuid: UUID = Field(default_factory=uuid4)
