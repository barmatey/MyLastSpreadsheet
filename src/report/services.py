from abc import ABC, abstractmethod
from uuid import UUID
from src.base.repo import repository

from . import domain
from ..spreadsheet.domain import CellValue


class SourceRepo(ABC):
    @property
    def source_info_repo(self) -> repository.Repository[domain.SourceInfo]:
        raise NotImplemented

    @property
    def wire_repo(self) -> repository.Repository[domain.Wire]:
        raise NotImplemented

    @abstractmethod
    async def add_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        raise NotImplemented


class SourceService:
    def __init__(self, repo: SourceRepo):
        self._repo = repo

    async def create_source(self, source: domain.Source):
        await self._repo.add_source(source)

    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        return await self._repo.get_source_by_id(uuid)

    async def append_wires(self, wires: list[domain.Wire]):
        await self._repo.wire_repo.add_many(wires)


class GroupGateway(ABC):

    @abstractmethod
    async def create_sheet(self, table: list[list[CellValue]]) -> UUID:
        raise NotImplemented


class CreateGroupUsecase:
    def __init__(self, repo: repository.Repository[domain.Group], gateway: GroupGateway):
        self._gateway = gateway
        self._repo = repo

    async def execute(self, title: str, source: domain.Source, ccols: list[domain.Ccol]) -> domain.Group:
        plan_items = domain.PlanItems(ccols=ccols)
        table = []
        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in plan_items.ccols]
            table.append(cells)
            key = str(cells)
            if plan_items.uniques.get(key) is None:
                plan_items.uniques[key] = 0
            plan_items.uniques[key] += 1

        sheet_id = await self._gateway.create_sheet(table)
        sheet_info = domain.SheetInfo(id=sheet_id)
        group = domain.Group(title=title, plan_items=plan_items, source_info=source.source_info, sheet_info=sheet_info)
        return group
