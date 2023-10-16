from abc import ABC
from uuid import UUID

from ..base.repo import repository
from src.spreadsheet import services as sheet_services
from . import domain as report_domain


class SourceRepo(ABC):
    @property
    def source_info_repo(self) -> repository.Repository[report_domain.Source]:
        raise NotImplemented

    @property
    def wire_repo(self) -> repository.Repository[report_domain.Wire]:
        raise NotImplemented


class SourceService:
    def __init__(self, repo: SourceRepo):
        self._repo = repo

    async def create_source(self, source: report_domain.Source):
        await self._repo.source_info_repo.add_many([source])

    async def get_source_by_id(self, uuid: UUID) -> report_domain.Source:
        return await self._repo.source_info_repo.get_one_by_id(uuid)

    async def append_wires(self, wires: list[report_domain.Wire]):
        await self._repo.wire_repo.add_many(wires)


class CreateGroup:
    def __init__(self, sheet_service: sheet_services.SheetService, group_repo: repository.Repository):
        self._group_repo = group_repo
        self._sheet_service = sheet_service

    async def execute(self, source: report_domain.Source, ccols: list[report_domain.Ccol]) -> report_domain.Group:
        plan_items = report_domain.PlanItems(ccols=ccols)

        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in plan_items.ccols]
            key = str(cells)
            plan_items.uniques[key] += 1 if plan_items.uniques.get(key) is not None else 1
            plan_items.table.append(cells)

        sheet = await self._sheet_service.create_sheet(plan_items.table)
        group = report_domain.Group(sheet_id=sheet.sf.id, plan_items=plan_items)
        await self._group_repo.add_many([group])

        return group
