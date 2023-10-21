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
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    receiver: services.SourceService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.append_wires(self.source_info, self.wires)


class DeleteWires(BaseModel):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    receiver: services.SourceService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.delete_wires(self.source_info,  self.wires)


class UpdateWires(BaseModel):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    receiver: services.SourceService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.update_wires(self.source_info, self.wires)


class CreateReport(BaseModel):
    source: domain.Source
    periods: list[domain.Period]
    plan_items: domain.PlanItems
    receiver: services.ReportService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Report:
        report = await self.receiver.create(source=self.source, plan_items=self.plan_items, periods=self.periods)
        return report


class GetReportById(BaseModel):
    id: UUID
    receiver: services.ReportService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Report:
        return await self.receiver.get_by_id(self.id)
