from uuid import UUID

from src.bus.broker import Broker
from src.bus.eventbus import EventBus
from .entity import Sheet

from .repository import SheetRepo, SheetRepoFake
from .subscriber import SheetSubscriber
from . import events

bus = EventBus()


@bus.register(events.SheetDeleted)
def handle_sheet_deleted(event: events.SheetDeleted, repo: SheetRepo = SheetRepoFake()):
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


def create_sheet(repo: SheetRepo = SheetRepoFake()) -> UUID:
    sheet = Sheet()
    repo.add(sheet)
    return sheet.uuid


def update_sheet(sheet: Sheet, repo: SheetRepo = SheetRepoFake()):
    repo.update(sheet)
