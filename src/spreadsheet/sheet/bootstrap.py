from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.broker import Broker
from src.bus.eventbus import EventBus
from src.spreadsheet.sheet import (
    events as sheet_events,
    services as sheet_services,
    repository as sheet_repo,
)
from src.spreadsheet.sindex import (
    events as sindex_events,
    services as sindex_services,
    repository as sindex_repo,
)
from src.spreadsheet.cell import (
    events as cell_events,
    services as cell_services,
    repository as cell_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._sheet_repo = sheet_repo.SheetRepoPostgres(session)
        self._sindex_repo = sindex_repo.SindexRepoPostgres(session)
        self._cell_repo = cell_repo.CellRepoPostgres(session)
        self._broker = Broker()

    def get_event_bus(self) -> EventBus:
        bus = EventBus()

        handler = sheet_services.SheetHandler(self._sheet_repo, self._broker)
        bus.add_handler(sheet_events.SheetCreated, handler.handle_sheet_created)

        handler = sindex_services.SindexHandler(self._sindex_repo, self._broker)
        bus.add_handler(sindex_events.SindexCreated, handler.handle_sindex_created)
        bus.add_handler(sindex_events.SindexUpdated, handler.handle_sindex_updated)
        bus.add_handler(sindex_events.SindexDeleted, handler.handle_sindex_deleted)
        bus.add_handler(sindex_events.SindexSubscribed, handler.handle_sindex_subscribed)

        handler = cell_services.CellHandler(self._cell_repo, self._broker)
        bus.add_handler(cell_events.CellCreated, handler.handle_cell_created)
        bus.add_handler(cell_events.CellUpdated, handler.handle_cell_updated)
        bus.add_handler(cell_events.CellDeleted, handler.handle_cell_deleted)
        bus.add_handler(cell_events.CellSubscribed, handler.handle_cell_subscribed)
        bus.add_handler(cell_events.CellUnsubscribed, handler.handle_cell_unsubscribed)

        return bus
