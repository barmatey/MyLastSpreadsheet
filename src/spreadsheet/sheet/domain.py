from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def size_factory():
    return 0, 0


class Sheet(BaseModel):
    size: tuple[int, int] = Field(default_factory=size_factory)
    uuid: UUID = Field(default_factory=uuid4)
