from uuid import UUID

from pydantic import BaseModel


class Entity(BaseModel):
    id: UUID

    def __hash__(self):
        return self.id.__hash__()