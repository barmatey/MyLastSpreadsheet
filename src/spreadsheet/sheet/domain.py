from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Sheet(BaseModel):
    size: tuple[int, int] = Field(default_factory=lambda x: (0, 0))
    uuid: UUID = Field(default_factory=uuid4)
