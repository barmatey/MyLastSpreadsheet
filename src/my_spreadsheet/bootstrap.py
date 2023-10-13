from src.my_spreadsheet import eventbus
from . import domain
from . import services
from .broker import BrokerService
from .infrastructure import postgres, subfactory


class Bootstrap:
    def __init__(self, session):
        self._queue = eventbus.Queue()
        self._sheet_repo: services.SheetRepository = postgres.SheetPostgresRepo(session)

        self._sheet_service = services.SheetService(self._sheet_repo, self._queue)

        self._broker = BrokerService()
        self._subfac = subfactory.SubFactory(self._sheet_service, self._broker)

    def get_event_bus(self) -> eventbus.EventBus:
        bus = eventbus.EventBus(self._queue)

        handler = services.CellHandler(self._subfac, self._broker)
        bus.register("CellUpdated", handler.handle_cell_updated)

        handler = services.SindexHandler(self._subfac, self._broker)
        bus.register("SindexUpdated", handler.handle_sindex_updated)

        return bus

    def get_sheet_service(self) -> services.SheetService:
        return self._sheet_service

    def get_subfac(self) -> subfactory.SubFactory:
        return self._subfac
