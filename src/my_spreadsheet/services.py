from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from src.core import OrderBy
from . import domain
from . import subscriber
from . import eventbus
from .broker import BrokerService

T = TypeVar("T", bound=domain.BaseModel)


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add_many(self, data: list[T]):
        raise NotImplemented

    @abstractmethod
    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        raise NotImplemented

    @abstractmethod
    async def update_one(self, data: T):
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, data: list[T]):
        raise NotImplemented


class Service(ABC, Generic[T]):
    def __init__(self, repo: Repository[T], queue: eventbus.Queue):
        self._queue = queue
        self._repo = repo

    async def create_many(self, data: list[T]):
        await self._repo.add_many(data)

    async def get_many_by_ids(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        return await self._repo.get_many_by_id(ids, order_by)

    async def update_one(self, entity: T, old_entity: T = None):
        if old_entity is None:
            old_entity = (await self.get_many_by_ids(entity.id)).pop()
        await self._repo.update_one(entity)
        self._notify_updated(old_entity, entity)

    async def delete_one(self, entity: T):
        await self._repo.remove_many([entity])
        self._notify_deleted(entity)

    def _notify_updated(self, old_entity: T, new_entity: T):
        key = f"{old_entity.__class__.__name__}Updated"
        event = eventbus.Updated(key=key, old_entity=old_entity, actual_entity=new_entity)
        self._queue.append(event)

    def _notify_deleted(self, entity: T):
        key = f"{entity.__class__.__name__}Deleted"
        event = eventbus.Deleted(key=key, entity=entity)
        self._queue.append(event)


class SheetService:
    def __init__(self, repo: Repository[domain.Sheet]):
        self._repo = repo

    async def create_sheet(self, table: list[list[domain.CellValue]]) -> domain.Sheet:
        size = (len(table), len(table[0])) if len(table) else (0, 0)
        sf = domain.SheetInfo(size=size)

        row_sindexes = [domain.RowSindex(sheet_info=sf, position=i) for i in range(0, size[0])]
        col_sindexes = [domain.ColSindex(sheet_info=sf, position=j) for j in range(0, size[1])]

        cells = []
        for i, row in enumerate(table):
            for j, cell_value in enumerate(row):
                cells.append(domain.Cell(sheet_info=sf, row=row_sindexes[i], col=col_sindexes[j], value=cell_value))

        sheet = domain.Sheet(sf=sf, rows=row_sindexes, cols=col_sindexes, cells=cells, id=sf.id)
        await self._repo.add_many([sheet])
        return sheet

    async def get_sheet_by_uuid(self, uuid: UUID) -> domain.Sheet:
        return (await self._repo.get_many_by_id([uuid])).pop()

    async def delete_rows(self, rows: list[domain.RowSindex]):
        raise NotImplemented

    async def delete_cols(self, cols: list[domain.ColSindex]):
        raise NotImplemented


class Handler:
    def __init__(self, sub_factory: subscriber.SubscriberFactory, broker: BrokerService):
        self._sub_factory = sub_factory
        self._broker = broker


class CellHandler(Handler):
    async def handle_cell_updated(self, event: eventbus.Updated[domain.Cell]):
        subs: list[subscriber.CellSubscriber] = [self._sub_factory.create_cell_subscriber(x)
                                                 for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_cell_updated(old=event.old_entity, actual=event.actual_entity)


class SindexHandler(Handler):
    async def handle_sindex_updated(self, event: eventbus.Updated[domain.Sindex]):
        subs = [self._sub_factory.create_sindex_subscriber(x) for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_sindex_updated(event.old_entity, event.actual_entity)
