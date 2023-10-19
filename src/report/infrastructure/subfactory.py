from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber, GroupSubscriber
from .. import domain, services, events
from ...base import eventbus
from ...base.broker import BrokerService


class GroupPublisher(SourceSubscriber):
    def __init__(self, entity: domain.Group, broker: BrokerService, queue: eventbus.Queue):
        self._queue = queue
        self._broker = broker
        self._entity = entity
        self.__appended_rows: list[list[domain.CellValue]] = []

    def __append_wire(self, wire: domain.Wire):
        cells = [wire.__getattribute__(ccol) for ccol in self._entity.plan_items.ccols]
        key = str(cells)
        if self._entity.plan_items.uniques.get(key) is None:
            self._entity.plan_items.uniques[key] = 0
            self.__appended_rows.append(cells)
            self._entity.plan_items.table.append(cells)
        self._entity.plan_items.uniques[key] += 1

    async def follow_source(self, source: domain.Source):
        self._entity.plan_items.uniques = {}
        self._entity.plan_items.table = []
        for wire in source.wires:
            self.__append_wire(wire)
        await self._broker.subscribe([source.source_info], self._entity)
        self._queue.append(
            events.GroupRowsAppended(key='GroupRowsInserted', rows=self.__appended_rows, group_info=self._entity))

    async def on_wires_appended(self, wires: list[domain.Wire]):
        for wire in wires:
            self.__append_wire(wire)
        self._queue.append(
            events.GroupRowsAppended(key='GroupRowsInserted', rows=self.__appended_rows, group_info=self._entity))


class ReportPublisher(SourceSubscriber, GroupSubscriber):
    def __init__(self, entity: domain.Report, report_service: services.ReportService, broker: BrokerService):
        self._entity = entity
        self._broker = broker
        self._service = report_service

    async def follow_source(self, source: domain.Source):
        for wire in source.wires:
            pass
        await self._broker.subscribe([source], self._entity)

    async def on_wires_appended(self, wire: domain.Wire):
        raise NotImplemented

    async def follow_group(self, group: domain.Group):
        await self._broker.subscribe([group], self._entity)

    async def on_rows_appended(self, data: list[list[domain.CellValue]]):
        raise NotImplemented


class ReportSubfac(SubscriberFactory):
    def __init__(self, report_service: services.ReportService, broker: BrokerService, queue: eventbus.Queue):
        self._broker = broker
        self._queue = queue
        self._report_service = report_service

    def create_group_subscriber(self, entity: BaseModel) -> GroupSubscriber:
        if isinstance(entity, domain.Report):
            return ReportPublisher(entity, self._report_service, self._broker)
        raise TypeError(f"{type(entity)}")

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.Group):
            return GroupPublisher(entity, self._broker, self._queue)
        if isinstance(entity, domain.Report):
            return ReportPublisher(entity, self._report_service, self._broker)
        raise TypeError


