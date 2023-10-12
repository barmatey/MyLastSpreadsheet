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
    def __init__(self, sf_service: Service[domain.SheetInfo], sindex_service: Service[domain.Sindex],
                 cell_service: Service[domain.Cell]):
        self.sf_service = sf_service
        self.sindex_service = sindex_service
        self.cell_service = cell_service

    async def create_sheet(self, table: list[list[domain.CellValue]]):
        raise NotImplemented

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


class CellSelfSubscriber(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Cell, sheet_service: SheetService, broker_service: BrokerService):
        self._sheet_service = sheet_service
        self._broker_service = broker_service
        self._entity = entity

    async def follow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = pubs[0].value
        await self._broker_service.subscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_one(self._entity, old)

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = None
        await self._broker_service.unsubscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_one(self._entity, old)

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        self._entity.value = actual.value
        await self._sheet_service.cell_service.update_one(old, actual)

    async def on_cell_deleted(self, pub: domain.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        await self._sheet_service.cell_service.update_one(self._entity, old)


class SindexSelfSubscriber(subscriber.SindexSubscriber):
    def __init__(self, entity: domain.Sindex, sheet_service: SheetService, broker_service: BrokerService):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sindexes(self, pubs: list[domain.Sindex]):
        await self._broker_service.subscribe(pubs, self._entity)

    async def unfollow_sindexes(self, pubs: list[domain.Sindex]):
        raise NotImplemented

    async def on_sindex_updated(self, old_value: domain.Sindex, new_value: domain.Sindex):
        pass

    async def on_sindex_deleted(self, pub: domain.Sindex):
        await self._sheet_service.sindex_service.delete_one(self._entity)


class SheetSelfSubscriber(subscriber.SheetSubscriber):
    def __init__(self, entity: domain.Sheet, sheet_service: SheetService, broker_service: BrokerService):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sheet(self, pub: domain.Sheet):
        if self._entity.sheet_info.size != (0, 0):
            raise ValueError

        # Change sheet size
        old = self._entity.sf.model_copy(deep=True)
        self._entity.sf.size = pub.sf.size
        await self._sheet_service.sf_service.update_one(entity=self._entity.sf, old_entity=old)

        # Create table
        rows = [domain.RowSindex(position=x.position, sheet_info=self._entity.sf) for x in pub.rows]
        cols = [domain.ColSindex(position=x.position, sheet_info=self._entity.sf) for x in pub.cols]
        cells = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                value = pub.cells[i * pub.sheet_info.size[1] + j].value
                cells.append(domain.Cell(sheet_info=self._entity.sheet_info, row=row, col=col, value=value))
        await self._sheet_service.sindex_service.create_many(rows)
        await self._sheet_service.sindex_service.create_many(cols)
        await self._sheet_service.cell_service.create_many(cells)

        # Subscribe
        for parent, child in zip(pub.rows, rows):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cols, cols):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cells, cells):
            await self._broker_service.subscribe([parent], child)

    async def unfollow_sheet(self, pub: domain.Sheet):
        raise NotImplemented

    async def on_rows_appended(self, table: list[list[domain.CellValue]]):
        raise NotImplemented

    async def on_sheet_deleted(self):
        raise NotImplemented
