from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.eventbus import EventBus
from src.spreadsheet.sindex import (
    events as sindex_events,
    handlers as sindex_handlers,
    repository as sindex_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._sindex_repo = sindex_repo.SindexRepoPostgres(session)

    def get_event_bus(self) -> EventBus:
        bus = EventBus()
        repo = {"repo": self._sindex_repo}
        bus.add_handler(sindex_events.SindexCreated, sindex_handlers.handle_sindex_created, repo)
        bus.add_handler(sindex_events.SindexUpdated, sindex_handlers.handle_sindex_updated, repo)
        bus.add_handler(sindex_events.SindexDeleted,  sindex_handlers.handle_sindex_deleted, repo)
        bus.add_handler(sindex_events.SindexSubscribed, sindex_handlers.handle_sindex_subscribed, repo)
        return bus
