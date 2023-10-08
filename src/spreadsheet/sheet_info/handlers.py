from src.bus.broker import Broker
from src.bus.eventbus import EventBus

from .repository import SheetMetaRepo, SheetMetaRepoFake
from src.spreadsheet.sheet.subscriber import SheetSubscriber
from ..sheet import events

bus = EventBus()


@bus.register(events.SheetDeleted)
def handle_sheet_deleted(event: events.SheetDeleted, repo: SheetMetaRepo = SheetMetaRepoFake()):
    subs: set[SheetSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        sub.on_sheet_deleted()
    repo.remove_one(event.entity)


@bus.register(events.SheetSubscribed)
def handle_sheet_subscribed(event: events.SheetSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


@bus.register(events.SheetUnsubscribed)
def handle_sheet_unsubscribed(event: events.SheetUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
