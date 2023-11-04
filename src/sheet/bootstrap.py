import src.sheet.handlers
from src.base.broker import Broker, BrokerRepoPostgres
from ..base import eventbus
from . import services, domain
from .infrastructure import postgres, subfactory


class Bootstrap:
    def __init__(self, session):
        self._queue = eventbus.Queue()
        self._broker = Broker(BrokerRepoPostgres(session))

        self._sheet_repo: services.SheetRepository = postgres.SheetPostgresRepo(session)
        cell_service = services.CellService(self._sheet_repo)
        formula_service = services.FormulaService(self._sheet_repo, self._broker)
        self._sheet_service = services.SheetService(self._sheet_repo, cell_service, formula_service)

        self._subfac = subfactory.SubFactory(self._sheet_service, self._broker)
        self._report_sheet_service = services.ReportSheetService(repo=self._sheet_repo, subfac=self._subfac)

    def get_event_bus(self) -> eventbus.EventBus:
        bus = eventbus.EventBus(self._queue)

        handler = src.sheet.handlers.CellHandler(self._subfac, self._broker)
        bus.register("CellUpdated", handler.handle_cell_updated)
        bus.register("CellDeleted", handler.handle_cell_deleted)

        handler = src.sheet.handlers.SindexHandler(self._subfac, self._broker)
        bus.register("SindexUpdated", handler.handle_sindex_updated)
        bus.register("SindexDeleted", handler.handle_sindex_deleted)

        return bus

    def get_sheet_service(self) -> services.SheetService:
        return self._sheet_service

    def get_report_sheet_service(self) -> services.ReportSheetService:
        return self._report_sheet_service

    def get_subfac(self) -> subfactory.SubFactory:
        return self._subfac

    def get_broker(self) -> Broker:
        self._broker.register(domain.RowSindex, self._sheet_repo.row_repo.get_many_by_id)
        self._broker.register(domain.ColSindex, self._sheet_repo.col_repo.get_many_by_id)
        self._broker.register(domain.Cell, self._sheet_repo.cell_repo.get_many_by_id)
        return self._broker
