from src.bus.eventbus import EventBus
from src.bus.broker import Broker

from .repository import CellRepo
from .subscriber import CellSubscriber
from . import events

bus = EventBus()


@bus.register(events.CellCreated)
async def handle_cell_created(event: events.CellCreated, repo: CellRepo):
    await repo.add(cell=event.entity)


@bus.register(events.CellUpdated)
async def handle_cell_updated(event: events.CellUpdated, repo: CellRepo):
    repo.update_one(event.new_entity)

    subs: set[CellSubscriber] = Broker().get_subscribers(event.old_entity)
    for sub in subs:
        await sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)


@bus.register(events.CellDeleted)
async def handle_cell_deleted(event: events.CellDeleted, repo: CellRepo):
    repo.delete_one(event.entity)
    subs: set[CellSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        await sub.on_cell_deleted(event.entity)


@bus.register(events.CellSubscribed)
def handle_cell_subscribed(event: events.CellSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


@bus.register(events.CellUnsubscribed)
def handle_cell_unsubscribed(event: events.CellUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
