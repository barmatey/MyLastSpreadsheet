from uuid import UUID, uuid4
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed


def size_factory():
    return 0, 0


class Sheet(BaseModel):
    size: tuple[int, int] = Field(default_factory=size_factory)
    uuid: UUID = Field(default_factory=uuid4)


