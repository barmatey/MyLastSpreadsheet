from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber
from .. import domain, services
from ...base.broker import BrokerService


class GroupPublisher(SourceSubscriber):
    def __init__(self, entity: domain.Group, broker: BrokerService):
        self._broker = broker
        self._entity = entity

    async def follow_source(self, source: domain.Source):
        self._entity.plan_items.uniques = {}
        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in self._entity.plan_items.ccols]
            self._entity.plan_items.table.append(cells)
            key = str(cells)
            if self._entity.plan_items.uniques.get(key) is None:
                self._entity.plan_items.uniques[key] = 1
        await self._broker.subscribe([source.source_info], self._entity)

    async def on_wires_appended(self, wire: domain.Wire):
        raise NotImplemented


class ReportSubscriber(SourceSubscriber):
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


class ReportSubfac(SubscriberFactory):
    def __init__(self, report_service: services.ReportService, broker: BrokerService):
        self._broker = broker
        self._report_service = report_service

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.Group):
            return GroupPublisher(entity, self._broker)
        if isinstance(entity, domain.Report):
            return ReportSubscriber(entity, self._report_service, self._broker)
        raise TypeError
