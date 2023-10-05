from src.bus.broker import Broker
from src.bus.eventbus import EventBus

from .domain import SheetCreated, SheetUpdated, SheetDeleted, SheetSubscribed, SheetUnsubscribed
from .pubsub import SheetSubscriber
from .repository import SheetRepo, SheetRepoFake

bus = EventBus()


@bus.register(SheetCreated)
def handle_sheet_created(event: SheetCreated, repo: SheetRepo = SheetRepoFake()):
    repo.add(event.entity)


@bus.register(SheetUpdated)
def handle_sheet_updated(event: SheetUpdated, repo: SheetRepo = SheetRepoFake()):
    repo.update(event.new_entity)


@bus.register(SheetDeleted)
def handle_sheet_deleted(event: SheetDeleted, repo: SheetRepo = SheetRepoFake()):
    subs: set[SheetSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        sub.on_sheet_deleted()
    repo.remove_one(event.entity)


@bus.register(SheetSubscribed)
def handle_sheet_subscribed(event: SheetSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


@bus.register(SheetUnsubscribed)
def handle_sheet_unsubscribed(event: SheetUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
