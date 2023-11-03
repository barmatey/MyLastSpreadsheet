from uuid import UUID

from src.core import Table
from src.report import domain
from src.report.services import SheetGateway
from src.sheet import domain as sheet_domain, services as sheet_service


class SheetGatewayAPI(SheetGateway):
    def __init__(self, service: sheet_service.SheetService, report_sheet_service:  sheet_service.ReportSheetService):
        self._sheet_service = service
        self._report_sheet_service = report_sheet_service

    async def get_sheet_by_id(self, sheet_id: UUID) -> sheet_domain.Sheet:
        return await self._sheet_service.get_sheet_by_id(sheet_id)

    async def create_sheet(self, sheet: sheet_domain.Sheet = None) -> UUID:
        sheet = await self._sheet_service.create_sheet(sheet)
        return sheet.sf.id

    async def create_checker_sheet(self, base_sheet_id: UUID) -> UUID:
        sheet = await self._report_sheet_service.create_checker_sheet(base_sheet_id)
        return sheet.sf.id

    async def update_sheet(self, data: sheet_domain.Sheet):
        await self._sheet_service.update_sheet(data)

    async def merge_sheets(self, target_sheet_id: UUID, data: sheet_domain.Sheet, merge_on: list[int]):
        await self._sheet_service.complex_merge(target_sheet_id, data, merge_on, merge_on)
