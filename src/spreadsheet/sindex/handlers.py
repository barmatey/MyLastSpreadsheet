from src.bus.eventbus import EventBus
from src.bus.broker import Broker
from . import (
    events as sindex_events,
    repository as sindex_repo,
    subscriber as sindex_subscriber,
)

bus = EventBus()


@bus.register(sindex_events.SindexCreated)
async def handle_sindex_created(event: sindex_events.SindexCreated, repo: sindex_repo.SindexRepo):
    await repo.add(event.entity)


@bus.register(sindex_events.SindexDeleted)
async def handle_sindex_deleted(event: sindex_events.SindexDeleted, repo: sindex_repo.SindexRepo):
    subs: set[sindex_subscriber.SindexSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        await sub.on_sindex_deleted(event.entity)
    await repo.remove_one(event.entity)


@bus.register(sindex_events.SindexUpdated)
async def handle_sindex_updated(event: sindex_events.SindexUpdated, repo: sindex_repo.SindexRepo):
    subs: set[sindex_subscriber.SindexSubscriber] = Broker().get_subscribers(event.new_entity)
    for sub in subs:
        await sub.on_sindex_updated(event.old_entity, event.new_entity)
    await repo.update_one(event.new_entity)


@bus.register(sindex_events.SindexSubscribed)
async def handle_sindex_subscribed(event: sindex_events.SindexSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)
