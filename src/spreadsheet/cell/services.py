from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.cell import (
    entity as cell_entity,
    subscriber as cell_subscriber,
    events as cell_events,
)

from src.spreadsheet.sheet import (
    repository as sheet_repo,
)


class CellHandler:
    def __init__(self, repo: sheet_repo.SheetRepo, broker: Broker, queue: Queue):
        self._repo = repo
        self._broker = broker
        self._events = queue

    async def handle_cell_created(self, event: cell_events.CellCreated):
        raise NotImplemented

    async def handle_cell_updated(self, event: cell_events.CellUpdated):
        subs: set[cell_subscriber.CellSubscriber] = self._broker.get_subscribers(event.old_entity, self._repo,
                                                                                 self._events)
        for sub in subs:
            await sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)

    async def handle_cell_deleted(self, event: cell_events.CellDeleted):
        subs: set[cell_subscriber.CellSubscriber] = self._broker.get_subscribers(event.entity, self._repo, self._events)
        for sub in subs:
            await sub.on_cell_deleted(event.entity)

    async def handle_cell_subscribed(self, event: cell_events.CellSubscribed):
        self._broker.subscribe_to_many(event.pubs, event.sub)

    async def handle_cell_unsubscribed(self, event: cell_events.CellUnsubscribed):
        raise NotImplemented


class CellService:
    def __init__(self, repo: sheet_repo.SheetRepo, queue: Queue):
        self._repo = repo
        self._queue = queue

    async def create_cell(self, cell: cell_entity.Cell):
        await self._repo.cell_repo.add(cell)

    async def subscribe_cell(self, pubs, sub: cell_entity.Cell):
        sub = CellSelfSubscriber(sub, self._repo, self._queue)
        self._queue.append(cell_events.CellSubscribed(pubs=pubs, sub=sub))

    async def delete_cells(self, cells: list[cell_entity.Cell]):
        await self._repo.cell_repo.remove_many(cells)
        for cell in cells:
            self._queue.append(cell_events.CellDeleted(entity=cell))


class CellSelfSubscriber(cell_subscriber.CellSubscriber):
    def __init__(self, entity: cell_entity.Cell, repo: sheet_repo.SheetRepo, queue: Queue):
        self._entity = entity
        self._repo = repo
        self._cell_events = queue

    @property
    def entity(self):
        return self._entity

    async def follow_cells(self, pubs: list[cell_entity.Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def unfollow_cells(self, pubs: list[cell_entity.Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = None
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_updated(self, old: cell_entity.Cell, actual: cell_entity.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = actual.value
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))

    async def on_cell_deleted(self, pub: cell_entity.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        self._cell_events.append(cell_events.CellUpdated(old_entity=old, new_entity=self._entity))
