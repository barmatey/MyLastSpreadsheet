from src.bus.eventbus import EventBus
from . import events as sindex_events
from .repository import SindexRepo
from .subscriber import SindexSubscriber
from ...bus.broker import Broker

bus = EventBus()


@bus.register(sindex_events.SindexCreated)
async def handle_sindex_created(event: sindex_events.SindexCreated, repo: SindexRepo):
    await repo.add(event.entity)


@bus.register(sindex_events.SindexDeleted)
async def handle_sindex_deleted(event: sindex_events.SindexDeleted, repo: SindexRepo):
    subs: set[SindexSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        await sub.on_sindex_deleted(event.entity)
    await repo.remove_one(event.entity)


@bus.register(sindex_events.SindexUpdated)
async def handle_sindex_updated(event: sindex_events.SindexUpdated, repo: SindexRepo):
    subs: set[SindexSubscriber] = Broker().get_subscribers(event.new_entity)
    for sub in subs:
        await sub.on_sindex_updated(event.old_entity, event.new_entity)
    await repo.update_one(event.new_entity)


@bus.register(sindex_events.SindexSubscribed)
async def handle_sindex_subscribed(event: sindex_events.SindexSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)
