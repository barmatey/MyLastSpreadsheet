from src.bus.eventbus import EventBus
from src.bus.broker import Broker

from .domain import CellCreated, CellUpdated, CellSubscribed, CellUnsubscribed, CellDeleted, CellSubscriber
from .repository import CellRepo, CellRepoFake

bus = EventBus()


@bus.register(CellCreated)
def handle_cell_created(event: CellCreated, repo: CellRepo = CellRepoFake()):
    repo.add(event.entity)


@bus.register(CellUpdated)
def handle_cell_updated(event: CellUpdated, repo: CellRepo = CellRepoFake()):
    repo.update_one(event.new_entity)

    subs: list[CellSubscriber] = Broker().get_subscribers(event.new_entity)
    for sub in subs:
        sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)


@bus.register(CellDeleted)
def handle_cell_deleted(event: CellDeleted, repo: CellRepo = CellRepoFake()):
    repo.delete_one(event.entity)
    subs: list[CellSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        sub.on_cell_deleted(event.entity)


@bus.register(CellSubscribed)
def handle_cell_subscribed(event: CellSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


@bus.register(CellUnsubscribed)
def handle_cell_unsubscribed(event: CellUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
