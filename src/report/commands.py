from uuid import UUID

from pydantic import BaseModel

from . import domain, services


class CreateGroupSheet(BaseModel):
    source: domain.Source
    ccols: list[domain.Ccol]
    receiver: services.CreateGroupSheet

    async def execute(self) -> UUID:
        raise NotImplemented
