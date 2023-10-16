from uuid import UUID

from pydantic import BaseModel, ConfigDict

from . import domain, services


class CreateSource(BaseModel):
    title: str
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Source:
        source = domain.Source(title=self.title)
        await self.receiver.create_source(source)
        return source


# class CreateGroupSheet(BaseModel):
#     source: domain.Source
#     ccols: list[domain.Ccol]
#     receiver: services.CreateGroupSheet
#
#     async def execute(self) -> UUID:
#         raise NotImplemented
