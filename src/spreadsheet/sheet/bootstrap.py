from sqlalchemy.ext.asyncio import AsyncSession

from src.bus.broker import Broker
from src.bus.eventbus import EventBus, Queue
from src.spreadsheet.sheet import (
    events as sheet_events,
    entity as sheet_entity,
    subscriber as sheet_subscriber,
    services as sheet_services,
    repository as sheet_repo,
)
from src.spreadsheet.sindex import (
    events as sindex_events,
    services as sindex_services,
    repository as sindex_repo,
)
from src.spreadsheet.cell import (
    events as cell_events,
    services as cell_services,
    repository as cell_repo,
)
from src.spreadsheet.sheet_info import (
    events as sf_events,
    services as sf_services,
    repository as sf_repo,
)


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._sheet_repo = sheet_repo.SheetRepoPostgres(session)
        self._sindex_repo = sindex_repo.SindexRepoPostgres(session)
        self._cell_repo = cell_repo.CellRepoPostgres(session)
        self._sf_repo = sf_repo.SheetInfoRepoPostgres(session)
        self._broker = Broker()
        self._queue = Queue()

    def get_event_bus(self) -> EventBus:
        bus = EventBus(self._queue)

        handler = sheet_services.SheetHandler(self._sheet_repo, self._broker)
        bus.add_handler(sheet_events.SheetCreated, handler.handle_sheet_created)

        handler = sindex_services.SindexHandler(self._sindex_repo, self._broker, self._queue)
        bus.add_handler(sindex_events.SindexCreated, handler.handle_sindex_created)
        bus.add_handler(sindex_events.SindexUpdated, handler.handle_sindex_updated)
        bus.add_handler(sindex_events.SindexDeleted, handler.handle_sindex_deleted)
        bus.add_handler(sindex_events.SindexSubscribed, handler.handle_sindex_subscribed)

        handler = cell_services.CellHandler(self._cell_repo, self._broker, self._queue)
        bus.add_handler(cell_events.CellCreated, handler.handle_cell_created)
        bus.add_handler(cell_events.CellUpdated, handler.handle_cell_updated)
        bus.add_handler(cell_events.CellDeleted, handler.handle_cell_deleted)
        bus.add_handler(cell_events.CellSubscribed, handler.handle_cell_subscribed)
        bus.add_handler(cell_events.CellUnsubscribed, handler.handle_cell_unsubscribed)

        handler = sf_services.SheetInfoHandler(self._sf_repo, self._broker, self._queue)
        bus.add_handler(sf_events.SheetInfoUpdated, handler.handle_sheet_info_updated)

        return bus

    def get_sheet_service(self):
        return sheet_services.SheetService(self._sheet_repo, self._queue)

    def get_sindex_service(self):
        return sindex_services.SindexService(self._sindex_repo, self._queue)

    def get_sheet_subscriber(self, entity: sheet_entity.Sheet) -> sheet_subscriber.SheetSelfSubscriber:
        return sheet_subscriber.SheetSelfSubscriber(entity, self._sheet_repo, self._queue)
