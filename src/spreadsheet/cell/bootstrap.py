from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.eventbus import EventBus
from src.spreadsheet.cell import (
    events as cell_events,
    handlers as cell_handlers,
    repository as cell_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._cell_repo = cell_repo.CellRepoPostgres(session)

    def get_event_bus(self) -> EventBus:
        bus = EventBus()
        bus.add_handler(cell_events.CellCreated, cell_handlers.handle_cell_created, {"repo": self._cell_repo})
        bus.add_handler(cell_events.CellUpdated, cell_handlers.handle_cell_updated, {"repo": self._cell_repo})
        bus.add_handler(cell_events.CellDeleted,  cell_handlers.handle_cell_deleted, {"repo": self._cell_repo})
        bus.add_handler(cell_events.CellUnsubscribed, cell_handlers.handle_cell_subscribed, {"repo": self._cell_repo})
        bus.add_handler(cell_events.CellUnsubscribed, cell_handlers.handle_cell_unsubscribed, {"repo": self._cell_repo})
        return bus
