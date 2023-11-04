from pydantic import BaseModel

from src.base.broker import Broker
from .. import domain, subscriber, services
from ... import helpers


class SumFormula(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Formula, broker: Broker, sheet_service: services.SheetService):
        self._entity = entity
        self._broker = broker
        self._sheet_service = sheet_service

    async def follow_cells(self, pubs: list[domain.Cell]):
        for cell in pubs:
            self._entity.value += cell.value
        await self._sheet_service.formula_service.update_many([self._entity])
        await self._broker.subscribe(pubs, self._entity)

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        raise NotImplemented

    async def on_cell_deleted(self, pub: domain.Cell):
        raise NotImplemented


class CellSelfSubscriber(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Cell, sheet_service: services.SheetService, broker_service: Broker):
        self._sheet_service = sheet_service
        self._broker_service = broker_service
        self._entity = entity

    async def follow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        _old = self._entity.model_copy(deep=True)
        self._entity.value = pubs[0].value
        await self._broker_service.subscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_many([self._entity])

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        self._entity.value = actual.value
        await self._sheet_service.cell_service.update_many([actual])

    async def on_cell_deleted(self, pub: domain.Cell):
        _old = self._entity.model_copy()
        self._entity.value = "REF_ERROR"
        await self._sheet_service.cell_service.update_many([self._entity])


class SindexSelfSubscriber(subscriber.SindexSubscriber):
    def __init__(self, entity: domain.Sindex, sheet_service: services.SheetService, broker_service: Broker):
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


class SubFactory(subscriber.SubscriberFactory):
    def __init__(self, sheet_service: services.SheetService, broker_service: Broker):
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    def create_cell_subscriber(self, entity: BaseModel) -> subscriber.CellSubscriber:
        if isinstance(entity, domain.Cell):
            return CellSelfSubscriber(entity, self._sheet_service, self._broker_service)
        if isinstance(entity, domain.Sum):
            return entity
        raise TypeError

    def create_sindex_subscriber(self, entity: domain.Sindex) -> subscriber.SindexSubscriber:
        return SindexSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sheet_subscriber(self, entity: BaseModel) -> subscriber.SheetSubscriber:
        if isinstance(entity, domain.Sheet):
            return ReportCheckerSheet(entity, self._broker_service, self._sheet_service)
        raise TypeError
