from sqlalchemy.ext.asyncio import AsyncSession

from src.base.repo.repository import Repository
from . import services, domain
from .infrastructure import postgres, subfactory
from src.spreadsheet.bootstrap import Bootstrap as SheetBootstrap
from .infrastructure.gateway import SheetGatewayAPI
from ..base import eventbus


class Bootstrap(SheetBootstrap):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._source_repo: services.SourceRepo = postgres.SourceFullRepo(session)
        self._group_repo: Repository[domain.Group] = postgres.GroupRepo(session)
        self._report_repo: Repository[domain.Report] = postgres.ReportRepo(session)
        self._gw = SheetGatewayAPI(sheet_service=self.get_sheet_service())

        self._subfac = subfactory.ReportSubfac(self.get_report_service(), broker=self.get_broker(), queue=self._queue,
                                               sheet_gateway=self._gw)

    def get_source_service(self) -> services.SourceService:
        source_service = services.SourceService(repo=self._source_repo, queue=self._queue)
        return source_service

    def get_group_service(self) -> services.GroupService:
        usecase = services.GroupService(
            repo=self._group_repo,
            subfac=self._subfac
        )
        return usecase

    def get_report_service(self) -> services.ReportService:
        sheet_service = self.get_sheet_service()
        gw = SheetGatewayAPI(sheet_service=sheet_service)
        return services.ReportService(self._report_repo, gw, self._subfac)

    def get_event_bus(self) -> eventbus.EventBus:
        bus = super().get_event_bus()
        handler = services.SourceHandler(
            subfac=self._subfac,
            broker=self.get_broker()
        )
        bus.register('WiresAppended', handler.handle_wires_appended)

        handler = services.GroupHandler(self._subfac, self.get_broker())
        bus.register('GroupRowsInserted', handler.handle_group_rows_inserted)

        return bus
