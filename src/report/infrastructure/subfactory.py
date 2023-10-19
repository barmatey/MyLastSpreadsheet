from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber
from .. import domain, services


class PlanItemsSubscriber(SourceSubscriber):
    def __init__(self, entity: domain.PlanItems):
        self._entity = entity

    async def follow_source(self, source: domain.Source):
        self._entity.uniques = {}
        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in self._entity.ccols]
            self._entity.table.append(cells)
            key = str(cells)
            if self._entity.uniques.get(key) is None:
                self._entity.uniques[key] = 1

    async def on_wires_appended(self, wire: domain.Wire):
        raise NotImplemented


class ReportSubscriber(SourceSubscriber):
    def __init__(self, entity: domain.Report, report_service: services.ReportService):
        self._entity = entity
        self._service = report_service

    async def follow_source(self, source: domain.Source):
        for wire in source.wires:
            pass

    async def on_wires_appended(self, wire: domain.Wire):
        raise NotImplemented


class ReportSubfac(SubscriberFactory):
    def __init__(self, report_service: services.ReportService):
        self._report_service = report_service

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.PlanItems):
            return PlanItemsSubscriber(entity)
        if isinstance(entity, domain.Report):
            return ReportSubscriber(entity, self._report_service)
