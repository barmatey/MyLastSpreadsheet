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


class SheetRepository(ABC):
    @property
    def sheet_info_repo(self) -> Repository[domain.SheetInfo]:
        raise NotImplemented

    @property
    def row_repo(self) -> Repository[domain.RowSindex]:
        raise NotImplemented

    @property
    def col_repo(self) -> Repository[domain.ColSindex]:
        raise NotImplemented

    @property
    def cell_repo(self) -> Repository[domain.Cell]:
        raise NotImplemented

    @abstractmethod
    def add_sheet(self, sheet: domain.Sheet):
        raise NotImplemented

    @abstractmethod
    def get_sheet_by_id(self, uuid: UUID) -> domain.Sheet:
        raise NotImplemented


class SheetService:
    def __init__(self, repo: SheetRepository, queue: eventbus.Queue):
        self._repo = repo
        self._queue = queue

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
        await self._repo.add_sheet(sheet)
        return sheet

    async def update_cells(self, cells: list[domain.Cell], old_values: list[domain.Cell] = None):
        if old_values is None:
            ids = [x.id for x in cells]
            old_values = await self._repo.cell_repo.get_many_by_id(ids)
        if len(old_values) != len(cells):
            raise Exception
        for old, actual in zip(old_values, cells):
            await self._repo.cell_repo.update_one(actual)
            self._queue.append(eventbus.Updated(key="CellUpdated", old_entity=old, actual_entity=actual))

    async def delete_sindexes(self, sindexes: list[domain.Sindex]):
        raise NotImplemented

    async def get_sheet_by_uuid(self, uuid: UUID) -> domain.Sheet:
        return await self._repo.get_sheet_by_id(uuid)


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
