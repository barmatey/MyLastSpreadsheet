from src.my_spreadsheet import eventbus
from . import domain
from . import services
from .broker import BrokerService
from .infrastructure import postgres, subfactory


class Bootstrap:
    def __init__(self, session):
        self._queue = eventbus.Queue()
        self._sf_repo: services.Repository[domain.SheetInfo] = postgres.SheetInfoPostgresRepo(session)
        self._cell_repo: services.Repository[domain.Cell] = postgres.CellPostgresRepo(session)
        self._row_repo: services.Repository[domain.RowSindex] = postgres.RowPostgresRepo(session)
        self._col_repo: services.Repository[domain.ColSindex] = postgres.ColPostgresRepo(session)
        self._sheet_repo: services.Repository[domain.Sheet] = postgres.SheetPostgresRepo(session)

        self._sf_service: services.Service[domain.SheetInfo] = services.Service(self._sf_repo, self._queue)
        self._cell_service: services.Service[domain.Cell] = services.Service(self._cell_repo, self._queue)
        self._row_service: services.Service[domain.RowSindex] = services.Service(self._row_repo, self._queue)
        self._col_service: services.Service[domain.ColSindex] = services.Service(self._col_repo, self._queue)
        self._sheet_service = services.SheetService(self._sf_service, self._row_service, self._col_service,
                                                    self._cell_service)

    def get_event_bus(self) -> eventbus.EventBus:
        broker = BrokerService()
        bus = eventbus.EventBus(self._queue)
        subfac = subfactory.SubFactory(self._sheet_service, broker)

        handler = services.CellHandler(subfac, broker)
        bus.register("CellUpdated", handler.handle_cell_updated)

        handler = services.SindexHandler(subfac, broker)
        bus.register("SindexUpdated", handler.handle_sindex_updated)

        return bus

    def get_sheet_service(self) -> services.SheetService:
        return self._sheet_service
