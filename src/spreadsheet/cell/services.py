from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.cell import (
    entity as cell_entity,
    subscriber as cell_subscriber,
    events as cell_events,
    repository as cell_repo,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
    events as sf_events,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    repository as sindex_repo,
)


class CellHandler:
    def __init__(self, repo: cell_repo.CellRepo, broker: Broker, queue: Queue):
        self._repo = repo
        self._broker = broker
        self._events = queue

    async def handle_cell_created(self, event: cell_events.CellCreated):
        await self._repo.add(event.entity)

    async def handle_cell_updated(self, event: cell_events.CellUpdated):
        subs: set[cell_subscriber.CellSubscriber] = self._broker.get_subscribers(event.old_entity)
        for sub in subs:
            await sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)
        await self._repo.update_one(event.new_entity)

    async def handle_cell_deleted(self, event: cell_events.CellDeleted):
        subs: set[cell_subscriber.CellSubscriber] = Broker().get_subscribers(event.entity)
        for sub in subs:
            await sub.on_cell_deleted(event.entity)
        await self._repo.remove_many([event.entity])

    async def handle_cell_subscribed(self, event: cell_events.CellSubscribed):
        await cell_subscriber.CellSelfSubscriber(event.sub, self._repo, self._events).follow_cells(event.pubs)
        self._broker.subscribe_to_many(event.pubs, event.sub)

    async def handle_cell_unsubscribed(self, event: cell_events.CellUnsubscribed):
        self._broker.unsubscribe_from_many(event.pubs, event.sub)


class CellService:
    def __init__(self, repo: cell_repo.CellRepo, queue: Queue):
        self._repo = repo
        self._events = queue

    async def create_cell(self, cell: cell_entity.Cell):
        await self._events.append(cell_events.CellCreated(entity=cell))

    async def delete_cells(self, cells: list[cell_entity.Cell]):
        for cell in cells:
            self._events.append(cell_events.CellDeleted(entity=cell))
