from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.eventbus import EventBus
from src.spreadsheet.sheet import (
    events as sheet_events,
    repository as sheet_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._sheet_repo = sheet_repo.SheetRepoPostgres(session)

    def get_event_bus(self) -> EventBus:
        bus = EventBus()
        return bus
