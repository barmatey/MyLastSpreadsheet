from .. import domain
from .. import subscriber
from .. import services
from ..broker import BrokerService


class CellSelfSubscriber(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Cell, sheet_service: services.SheetService, broker_service: BrokerService):
        self._sheet_service = sheet_service
        self._broker_service = broker_service
        self._entity = entity

    async def follow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = pubs[0].value
        await self._broker_service.subscribe(pubs, self._entity)
        await self._cell_service.update_one(self._entity, old)

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = None
        await self._broker_service.unsubscribe(pubs, self._entity)
        await self._cell_service.update_one(self._entity, old)

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        self._entity.value = actual.value
        await self._cell_service.update_one(old, actual)

    async def on_cell_deleted(self, pub: domain.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        await self._cell_service.update_one(self._entity, old)


class SindexSelfSubscriber(subscriber.SindexSubscriber):
    def __init__(self, entity: domain.Sindex, sheet_service: services.SheetService, broker_service: BrokerService):
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
        raise NotImplemented


class SheetSelfSubscriber(subscriber.SheetSubscriber):
    def __init__(self, entity: domain.Sheet, sheet_service: services.SheetService, broker_service: BrokerService):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sheet(self, pub: domain.Sheet):
        self._entity = await self._sheet_service.merge(pub, self._entity)
        for parent, child in zip(pub.rows, self._entity.rows):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cols, self._entity.cols):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cells, self._entity.cells):
            await self._broker_service.subscribe([parent], child)

    async def unfollow_sheet(self, pub: domain.Sheet):
        raise NotImplemented

    async def on_rows_appended(self, table: list[list[domain.CellValue]]):
        raise NotImplemented

    async def on_sheet_deleted(self):
        raise NotImplemented


class SubFactory(subscriber.SubscriberFactory):
    def __init__(self, sheet_service: services.SheetService, broker_service: BrokerService):
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    def create_cell_subscriber(self, entity: domain.Cell) -> subscriber.CellSubscriber:
        return CellSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sindex_subscriber(self, entity: domain.Sindex) -> subscriber.SindexSubscriber:
        return SindexSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sheet_subscriber(self, entity: domain.Sheet) -> subscriber.SheetSubscriber:
        return SheetSelfSubscriber(entity, self._sheet_service, self._broker_service)
