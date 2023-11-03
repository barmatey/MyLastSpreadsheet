from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from . import domain, services
from ..core import OrderBy


class CreateSource(BaseModel):
    title: str
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Source:
        source = domain.Source(source_info=domain.SourceInfo(title=self.title))
        await self.receiver.create_source(source)
        return source


class GetSourceInfoById(BaseModel):
    id: UUID
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.SourceInfo:
        return await self.receiver.get_source_info_by_id(self.id)


class GetSourceById(BaseModel):
    id: UUID
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Source:
        return await self.receiver.get_source_by_id(self.id)


class GetSourceInfoList(BaseModel):
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> list[domain.SourceInfo]:
        return await self.receiver.get_source_info_list()


class DeleteSourceById(BaseModel):
    id: UUID
    receiver: services.SourceService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.delete_source_by_id(self.id)


class GetUniqueWires(BaseModel):
    receiver: services.SourceService
    fields: list[domain.Ccol]
    source_id: UUID
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> list[domain.Wire]:
        return await self.receiver.get_uniques(self.fields, filter_by={"source_id": self.source_id})


class GetWires(BaseModel):
    filter_by: dict
    receiver: services.SourceService
    order_by: OrderBy | None = None
    slice_from: int | None = None
    slice_to: int | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> list[domain.Wire]:
        return await self.receiver.get_wires(self.filter_by, self.order_by, self.slice_from, self.slice_to)


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
        await self.receiver.delete_wires(self.source_info, self.wires)


class UpdateWires(BaseModel):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    receiver: services.SourceService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.update_wires(self.source_info, self.wires)


class CreateReport(BaseModel):
    title: str
    source: domain.Source
    interval: domain.Interval
    plan_items: domain.PlanItems
    receiver: services.ReportService
    id: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Report:
        report = await self.receiver.create(
            title=self.title,
            source=self.source,
            plan_items=self.plan_items,
            interval=self.interval,
        )
        return report


class AppendCheckerSheet(BaseModel):
    report: domain.Report
    receiver: services.ReportService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Report:
        report = await self.receiver.append_checker_sheet(self.report)
        return report


class GetReportById(BaseModel):
    id: UUID
    receiver: services.ReportService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Report:
        return await self.receiver.get_by_id(self.id)


class GetReportList(BaseModel):
    receiver: services.ReportService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> list[domain.Report]:
        return await self.receiver.get_many()


class DeleteReportById(BaseModel):
    id: UUID
    receiver: services.ReportService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.delete_many(filter_by={"id": self.id})
