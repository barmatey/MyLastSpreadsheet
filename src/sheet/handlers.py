from src.base import eventbus
from src.base.broker import Broker
from src.sheet import domain, services


class Handler:
    def __init__(self, queue: eventbus.Queue, broker: Broker, repo: services.SheetRepository):
        self._queue = queue
        self._broker = broker
        self._repo = repo


class FormulaHandler(Handler):
    async def handle_formula_updated(self, event: eventbus.Updated[domain.Formula]):
        await self._repo.formula_repo.update_one(event.actual_entity)
        for sub in await self._broker.get_subs(event.actual_entity):
            await sub.on_cell_updated(old=event.old_entity, actual=event.actual_entity)
            self._queue.extend(sub.parse_events())


class CellHandler(Handler):
    async def handle_cell_updated(self, event: eventbus.Updated[domain.Cell]):
        await self._repo.cell_repo.update_one(event.actual_entity)
        for sub in await self._broker.get_subs(event.actual_entity):
            await sub.on_cell_updated(old=event.old_entity, actual=event.actual_entity)
            self._queue.extend(sub.parse_events())

    async def handle_cell_deleted(self, event: eventbus.Deleted[domain.Cell]):
        raise NotImplemented


class SindexHandler(Handler):
    async def handle_sindex_updated(self, event: eventbus.Updated[domain.Sindex]):
        raise NotImplemented

    async def handle_sindex_deleted(self, event: eventbus.Deleted[domain.Sindex]):
        raise NotImplemented
