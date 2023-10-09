from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    repository as sindex_repo,
    subscriber as sindex_subscriber,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
)


class SindexHandler:
    def __init__(self, broker: Broker):
        self._broker = broker

    async def handle_sindex_updated(self, event: sindex_events.SindexUpdated):
        subs: set[sindex_subscriber.SindexSubscriber] = self._broker.get_subscribers(event.new_entity)
        for sub in subs:
            await sub.on_sindex_updated(old_value=event.old_entity, new_value=event.new_entity)


class SindexService:
    def __init__(self, repo: sindex_repo.SindexRepo, events: Queue):
        self._events = events
        self._repo = repo

    async def create_row(self, sf: sf_entity.SheetInfo, position: int) -> sindex_entity.Sindex:
        sindex = sindex_entity.RowSindex(sheet_info=sf, position=position)
        await self._repo.add(sindex)
        return sindex

    async def update_row(self, sindex: sindex_entity.Sindex):
        old = await self._repo.get_one_by_uuid(sindex.uuid)
        await self._repo.update_one(sindex)
        self._events.append(sindex_events.SindexUpdated(old_entity=old, new_entity=sindex))


class SindexSelfSubscriber(sindex_subscriber.SindexSubscriber):
    def __init__(self, entity: sindex_entity.Sindex, queue: Queue):
        self._events = queue
        self._entity = entity

    async def follow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        self._events.append(sindex_events.SindexSubscribed(pubs=pubs, sub=self._entity))

    async def unfollow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        pass

    async def on_sindex_updated(self, old_value: sindex_entity.Sindex, new_value: sindex_entity.Sindex):
        pass

    async def on_sindex_deleted(self, pub: sindex_entity.Sindex):
        self._events.append(sindex_events.SindexDeleted(entity=self._entity))
        new_sheet = self._entity.sheet_info.model_copy(deep=True)
        new_sheet.size = (new_sheet.size[0] - 1, new_sheet.size[1])
        self._events.append(sheet_events.SheetSizeUpdated(old_entity=self._entity.sheet_info, new_entity=new_sheet))
