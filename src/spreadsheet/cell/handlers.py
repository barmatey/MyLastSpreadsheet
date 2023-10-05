from uuid import UUID, uuid4

from src.bus.eventbus import EventBus, Queue
from src.bus.broker import Broker
from .entity import CellValue, Cell

from ..sheet.entity import Sheet
from .repository import CellRepo, CellRepoFake
from .subscriber import CellSubscriber
from . import events


def create_cell(sheet: Sheet, value: CellValue, uuid: UUID = None, repo: CellRepo = CellRepoFake()) -> UUID:
    if uuid is None:
        uuid = uuid4()
    cell = Cell(sheet=sheet, value=value, uuid=uuid)
    repo.add(cell)
    return cell.uuid


bus = EventBus()


@bus.register(events.CellUpdated)
def handle_cell_updated(event: events.CellUpdated, repo: CellRepo = CellRepoFake()):
    repo.update_one(event.new_entity)

    subs: set[CellSubscriber] = Broker().get_subscribers(event.old_entity)
    for sub in subs:
        sub.on_cell_updated(old=event.old_entity, actual=event.new_entity)


@bus.register(events.CellDeleted)
def handle_cell_deleted(event: events.CellDeleted, repo: CellRepo = CellRepoFake()):
    repo.delete_one(event.entity)
    subs: set[CellSubscriber] = Broker().get_subscribers(event.entity)
    for sub in subs:
        sub.on_cell_deleted(event.entity)


@bus.register(events.CellSubscribed)
def handle_cell_subscribed(event: events.CellSubscribed):
    Broker().subscribe_to_many(event.pubs, event.sub)


@bus.register(events.CellUnsubscribed)
def handle_cell_unsubscribed(event: events.CellUnsubscribed):
    Broker().unsubscribe_from_many(event.pubs, event.sub)
