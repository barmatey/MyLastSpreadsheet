from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.broker import Broker
from src.bus.eventbus import EventBus
from src.spreadsheet.sindex import (
    events as sindex_events,
    services as sindex_services,
    repository as sindex_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession, broker: Broker):
        self._sindex_repo = sindex_repo.SindexRepoPostgres(session)
        self._broker = broker

    def get_event_bus(self) -> EventBus:
        bus = EventBus()
        handler = sindex_services.SindexHandler(self._sindex_repo, self._broker)
        bus.add_handler(sindex_events.SindexCreated, handler.handle_sindex_created)
        bus.add_handler(sindex_events.SindexUpdated, handler.handle_sindex_updated)
        bus.add_handler(sindex_events.SindexDeleted, handler.handle_sindex_deleted)
        bus.add_handler(sindex_events.SindexSubscribed, handler.handle_sindex_subscribed)
        return bus
