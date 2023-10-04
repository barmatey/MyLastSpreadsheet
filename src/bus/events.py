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
