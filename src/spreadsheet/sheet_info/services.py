from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
    events as sf_events,
    repository as sf_repo,
)
from src.spreadsheet.sheet import (
    repository as sheet_repo,
)


class SheetInfoHandler:
    def __init__(self, repo: sheet_repo.SheetRepo, broker: Broker, queue: Queue):
        self._repo = repo
        self._broker = broker
        self._events = queue

    async def handle_sheet_info_updated(self, event: sf_events.SheetInfoUpdated):
        await self._repo.sheet_info_repo.update(event.new_entity)
