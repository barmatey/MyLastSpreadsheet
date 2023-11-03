from sqlalchemy.ext.asyncio import AsyncSession

from src.base.repo.repository import Repository
from . import services, domain
from .infrastructure import postgres, subfactory
from src.sheet.bootstrap import Bootstrap as SheetBootstrap
from .infrastructure.gateway import SheetGatewayAPI
from ..base import eventbus
from ..base.broker import Broker


class Bootstrap(SheetBootstrap):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._source_repo: services.SourceRepo = postgres.SourceFullRepo(session)
        self._report_repo: Repository[domain.Report] = postgres.ReportRepo(session)
        self._gw = SheetGatewayAPI(service=self.get_sheet_service(),
                                   report_sheet_service=self.get_report_sheet_service())

        self._subfac = subfactory.ReportSubfac(broker=self.get_broker(),
                                               queue=self._queue,
                                               repo=self._report_repo,
                                               sheet_gateway=self._gw)

    def get_source_service(self) -> services.SourceService:
        source_service = services.SourceService(repo=self._source_repo, queue=self._queue)
        return source_service

    def get_report_service(self) -> services.ReportService:
        gw = SheetGatewayAPI(service=self.get_sheet_service(), report_sheet_service=self.get_report_sheet_service())
        return services.ReportService(self._report_repo, gw, self._subfac)

    def get_event_bus(self) -> eventbus.EventBus:
        bus = super().get_event_bus()
        handler = services.SourceHandler(
            subfac=self._subfac,
            broker=self.get_broker()
        )
        bus.register('WiresAppended', handler.handle_wires_appended)
        bus.register('WiresDeleted', handler.handle_wires_deleted)
        return bus

    def get_broker(self) -> Broker:
        broker = super().get_broker()
        broker.register(domain.Report, self._report_repo.get_many_by_id)
        return broker
