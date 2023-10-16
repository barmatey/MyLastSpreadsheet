from uuid import UUID

from pydantic import BaseModel, ConfigDict

from . import domain, services


class CreateSource(BaseModel):
    title: str
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Source:
        source = domain.Source(source_info=domain.SourceInfo(title=self.title))
        await self.receiver.create_source(source)
        return source


class GetSourceById(BaseModel):
    id: UUID
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Source:
        return await self.receiver.get_source_by_id(self.id)


# class CreateGroupSheet(BaseModel):
#     source: domain.Source
#     ccols: list[domain.Ccol]
#     receiver: services.CreateGroupSheet
#
#     async def execute(self) -> UUID:
#         raise NotImplemented
