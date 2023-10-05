from src.bus.eventbus import EventBus
from .domain import CellCreated, CellUpdated, CellSubscribed, CellUnsubscribed, CellDeleted, CellSubscriber
from .repository import CellRepo, CellRepoFake
from ...bus.broker import Broker

bus = EventBus()


@bus.register(CellCreated)
def handle_cell_created(event: CellCreated, repo: CellRepo = CellRepoFake()):
    repo.add(event.entity)


@bus.register(CellUpdated)
def handle_cell_updated(event: CellUpdated, repo: CellRepo = CellRepoFake()):
    repo.update_one(event.new_entity)

    subs = Broker().get_subscribers(event.new_entity)
