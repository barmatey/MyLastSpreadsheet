from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.eventbus import EventBus
from src.spreadsheet.sheet import (
    events as sheet_events,
    handlers as sheet_handlers,
    repository as sheet_repo,
)
from src.spreadsheet.sindex import (
    events as sindex_events,
    handlers as sindex_handlers,
    repository as sindex_repo,
)
from src.spreadsheet.cell import (
    events as cell_events,
    handlers as cell_handlers,
    repository as cell_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._sheet_repo = sheet_repo.SheetRepoPostgres(session)
        self._sindex_repo = sindex_repo.SindexRepoPostgres(session)
        self._cell_repo = cell_repo.CellRepoPostgres(session)

    def get_event_bus(self) -> EventBus:
        bus = EventBus()

        repo = {"repo": self._sheet_repo}
        bus.add_handler(sheet_events.SheetCreated, sheet_handlers.handle_sheet_created, repo)
        bus.add_handler(sheet_events.SheetRequested, sheet_handlers.handle_sheet_requested, repo)

        repo = {"repo": self._sindex_repo}
        bus.add_handler(sindex_events.SindexCreated, sindex_handlers.handle_sindex_created, repo)
        bus.add_handler(sindex_events.SindexUpdated, sindex_handlers.handle_sindex_updated, repo)
        bus.add_handler(sindex_events.SindexDeleted, sindex_handlers.handle_sindex_deleted, repo)
        bus.add_handler(sindex_events.SindexSubscribed, sindex_handlers.handle_sindex_subscribed)

        repo = {"repo": self._cell_repo}
        bus.add_handler(cell_events.CellCreated, cell_handlers.handle_cell_created, repo)
        bus.add_handler(cell_events.CellUpdated, cell_handlers.handle_cell_updated, repo)
        bus.add_handler(cell_events.CellDeleted, cell_handlers.handle_cell_deleted, repo)
        bus.add_handler(cell_events.CellSubscribed, cell_handlers.handle_cell_subscribed)
        bus.add_handler(cell_events.CellUnsubscribed, cell_handlers.handle_cell_unsubscribed)

        return bus
