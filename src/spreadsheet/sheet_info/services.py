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
        raise NotImplemented


class SheetInfoService:
    def __init__(self, repo: sheet_repo.SheetRepo, queue: Queue):
        self._repo = repo
        self._queue = queue

    async def create_sheet_info(self, entity: sf_entity.SheetInfo):
        await self._repo.sheet_info_repo.add(entity)

    async def update_sheet_info(self, entity: sf_entity.SheetInfo):
        await self._repo.sheet_info_repo.update(entity)