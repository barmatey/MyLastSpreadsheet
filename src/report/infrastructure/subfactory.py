from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber
from .. import domain


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

    async def on_wire_appended(self, wire: domain.Wire):
        pass


class ReportSubfac(SubscriberFactory):
    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.PlanItems):
            return PlanItemsSubscriber(entity)
