from abc import ABC, abstractmethod
from uuid import UUID

from src.base import repository
from src.spreadsheet import domain as sheet_domain, services as sheet_services
from . import domain as report_domain


class CreateGroupSheet:
    def __init__(self, sheet_service: sheet_services.SheetService, group_repo: repository.Repository):
        self._group_repo = group_repo
        self._sheet_service = sheet_service

    async def execute(self, source: report_domain.Source, ccols: list[report_domain.Ccol]) -> sheet_domain.Sheet:
        plan_items = report_domain.PlanItems(ccols=ccols)

        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in plan_items.ccols]
            key = str(cells)
            plan_items.uniques[key] += 1 if plan_items.uniques.get(key) is not None else 1
            plan_items.table.append(cells)

        sheet = await self._sheet_service.create_sheet(plan_items.table)
        group = report_domain.Group(sheet_id=sheet.sf.id, plan_items=plan_items)
        await self._group_repo.add_many([group])
