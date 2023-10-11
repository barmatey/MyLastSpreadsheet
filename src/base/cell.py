from abc import abstractmethod
from typing import Union
from uuid import UUID, uuid4

from pydantic import Field

from src.base.service import Entity, Service, ManyUpdated, ManyDeleted, Broker, SubscriberFactory, Updated, Subscriber, \
    RepoPostgres, Repository

CellValue = Union[int, float]


class Cell(Entity):
    value: CellValue
    uuid: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        return self.uuid.__hash__()


class CellSubscriber(Subscriber[Cell]):
    @abstractmethod
    async def follow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def unfollow_cells(self, pubs: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def on_cell_updated(self, old: Cell, actual: Cell):
        raise NotImplemented

    @abstractmethod
    async def on_cell_deleted(self, pub: Cell):
        raise NotImplemented


class CellHandler:
    def __init__(self, broker: Broker, sub_factory: SubscriberFactory):
        self._broker = broker
        self._factory = sub_factory

    def handle_cells_updated(self, event: Updated[Cell]):
        subs: list[CellSubscriber] = [self._factory.create_subscriber(x) for x in self._broker.get_subs(event.actual)]
        for sub in subs:
            sub.on_cell_updated(event.old, event.actual)


class CellService(Service[Cell]):
    async def update_many(self, data: list[Cell], old_values: list[Cell] = None):
        await super().update_many(data, old_values)
        self._queue.append(ManyUpdated(key="CellsUpdated", old=old_values, actual=data))

    async def delete_many(self, data: list[Cell]):
        await super().delete_many(data)
        self._queue.append(ManyDeleted(key="CellsDeleted", entities=data))


class CellSelfSubscriber(CellSubscriber):
    async def follow_cells(self, pubs: list[Cell]):
        old = self._entity.model_copy(deep=True)
        if len(pubs) != 1:
            raise Exception
        self._entity.value = pubs[0].value
        await self._service.update_many([self._entity], [old])
        self._broker.subscribe(pubs, self._entity)

    async def unfollow_cells(self, pubs: list[Cell]):
        pass

    async def on_cell_updated(self, old: Cell, actual: Cell):
        pass

    async def on_cell_deleted(self, pub: Cell):
        pass

