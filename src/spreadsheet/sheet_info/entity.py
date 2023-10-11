from uuid import UUID, uuid4
from pydantic import BaseModel, Field


def size_factory():
    return 0, 0


class SheetInfo(BaseModel):
    size: tuple[int, int] = Field(default_factory=size_factory)
    uuid: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.size}"

    def __repr__(self):
        return f"{self.size}"

    def __eq__(self, other):
        return all([
            self.size == other.size,
            self.uuid == other.uuid,
        ])
