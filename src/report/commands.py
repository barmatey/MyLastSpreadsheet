from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

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


class AppendWires(BaseModel):
    wires: list[domain.Wire]
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID = Field(default_factory=uuid4)

    async def execute(self) -> None:
        await self.receiver.append_wires(self.wires)
