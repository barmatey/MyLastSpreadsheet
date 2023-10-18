from src.spreadsheet import domain as sheet_domain
from ..subscriber import SourceSubscriber
from .. import domain as report_domain


class PlanItems(SourceSubscriber):
    def __init__(self, entity: report_domain.PlanItems):
        self._entity = entity

    async def follow_source(self, source: report_domain.Source):
        self._entity.uniques = {}
        for wire in source.wires:
            cells = [wire.__getattribute__(ccol) for ccol in self._entity.ccols]
            self._entity.table.append(cells)
            key = str(cells)
            if self._entity.uniques.get(key) is None:
                self._entity.uniques[key] = 1

    async def on_wire_appended(self, wire: report_domain.Wire):
        pass
