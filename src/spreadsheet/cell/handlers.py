from src.bus.broker import Broker

from .repository import CellRepo
from .subscriber import CellSubscriber
from . import events


async def handle_cell_created(event: events.CellCreated, repo: CellRepo):
    await repo.add(cell=event.entity)


async def handle_cell_updated(event: events.CellUpdated, repo: CellRepo):
    await repo.update_one(event.new_entity)

    subs: set[CellSubscriber] = Broker().get_subscribers(event.old_entity)
    for sub in subs:
        await sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)


async def handle_cell_deleted(event: events.CellDeleted, repo: CellRepo):
    await repo.delete_one(event.entity)
    subs: set[CellSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        await sub.on_cell_deleted(event.entity)


async def handle_cell_subscribed(event: events.CellSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


async def handle_cell_unsubscribed(event: events.CellUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
