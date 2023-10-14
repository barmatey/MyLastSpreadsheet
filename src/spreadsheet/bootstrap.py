from src.base.broker import BrokerService
from ..base import eventbus
from . import services
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
        bus.register("CellDeleted", handler.handle_cell_deleted)

        handler = services.SindexHandler(self._subfac, self._broker)
        bus.register("SindexUpdated", handler.handle_sindex_updated)
        bus.register("SindexDeleted", handler.handle_sindex_deleted)

        return bus

    def get_sheet_service(self) -> services.SheetService:
        return self._sheet_service

    def get_subfac(self) -> subfactory.SubFactory:
        return self._subfac
