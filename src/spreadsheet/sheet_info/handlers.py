from src.bus.broker import Broker

from src.spreadsheet.sheet.subscriber import SheetSubscriber
from .repository import SheetMetaRepo
from ..sheet import events


def handle_sheet_deleted(event: events.SheetDeleted, repo: SheetMetaRepo):
    subs: set[SheetSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        sub.on_sheet_deleted()
    repo.remove_one(event.entity)


def handle_sheet_subscribed(event: events.SheetSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


def handle_sheet_unsubscribed(event: events.SheetUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
