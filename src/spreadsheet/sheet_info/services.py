from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
    events as sf_events,
    repository as sf_repo,
)


class SheetInfoHandler:
    def __init__(self, repo: sf_repo.SheetInfoRepo, broker: Broker, queue: Queue):
        self._repo = repo
        self._broker = broker
        self._events = queue

    async def handle_sheet_info_updated(self, event: sf_events.SheetInfoUpdated):
        await self._repo.update(event.new_entity)
