from src.base import broker, eventbus
from . import subscriber, domain


class Handler:
    def __init__(self, sub_factory: subscriber.SubscriberFactory, broker_service: broker.Broker):
        self._sub_factory = sub_factory
        self._broker = broker_service


class CellHandler(Handler):
    async def handle_cell_updated(self, event: eventbus.Updated[domain.Cell]):
        subs = [self._sub_factory.create_cell_subscriber(x) for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_cell_updated(old=event.old_entity, actual=event.actual_entity)

    async def handle_cell_deleted(self, event: eventbus.Deleted[domain.Cell]):
        subs = [self._sub_factory.create_cell_subscriber(x) for x in await self._broker.get_subs(event.entity)]
        for sub in subs:
            await sub.on_cell_deleted(pub=event.entity)


class SindexHandler(Handler):
    async def handle_sindex_updated(self, event: eventbus.Updated[domain.Sindex]):
        subs = [self._sub_factory.create_sindex_subscriber(x) for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_sindex_updated(event.old_entity, event.actual_entity)

    async def handle_sindex_deleted(self, event: eventbus.Deleted[domain.Sindex]):
        subs = [self._sub_factory.create_sindex_subscriber(x) for x in await self._broker.get_subs(event.entity)]
        for sub in subs:
            await sub.on_sindex_deleted(pub=event.entity)
