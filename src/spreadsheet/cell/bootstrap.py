from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.broker import Broker
from src.bus.eventbus import EventBus
from src.spreadsheet.cell import (
    events as cell_events,
    services as cell_services,
    repository as cell_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._cell_repo = cell_repo.CellRepoPostgres(session)
        self._broker = Broker()

    def get_event_bus(self) -> EventBus:
        bus = EventBus()
        handler = cell_services.CellHandler(self._cell_repo, self._broker)
        bus.add_handler(cell_events.CellCreated, handler.handle_cell_created)
        bus.add_handler(cell_events.CellUpdated, handler.handle_cell_updated)
        bus.add_handler(cell_events.CellDeleted,  handler.handle_cell_deleted)
        bus.add_handler(cell_events.CellUnsubscribed, handler.handle_cell_subscribed)
        bus.add_handler(cell_events.CellUnsubscribed, handler.handle_cell_unsubscribed)
        return bus
