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
    def __init__(self, repo: sindex_repo.SindexRepo, broker: Broker, queue: Queue):
        self._broker = broker
        self._events = queue
        self._repo = repo

    async def handle_sindex_created(self, event: sindex_events.SindexCreated):
        await self._repo.add(event.entity)

    async def handle_sindex_updated(self, event: sindex_events.SindexUpdated):
        await self._repo.update_one(event.new_entity)
        subs: set[sindex_subscriber.SindexSubscriber] = self._broker.get_subscribers(event.new_entity)
        for sub in subs:
            await sub.on_sindex_updated(old_value=event.old_entity, new_value=event.new_entity)

    async def handle_sindex_deleted(self, event: sindex_events.SindexDeleted):
        subs: set[sindex_subscriber.SindexSubscriber] = self._broker.get_subscribers(event.entity)
        for sub in subs:
            await sub.on_sindex_deleted(event.entity)
        await self._repo.remove_one(event.entity)

    async def handle_sindex_subscribed(self, event: sindex_events.SindexSubscribed):
        await sindex_subscriber.SindexSelfSubscriber(event.sub, self._repo, self._events).follow_sindexes(event.pubs)
        self._broker.subscribe_to_many(event.pubs, event.sub)


class SindexService:
    def __init__(self, repo: sindex_repo.SindexRepo, events: Queue):
        self._events = events
        self._repo = repo

    async def create_row(self, sf: sf_entity.SheetInfo, position: int) -> sindex_entity.RowSindex:
        sindex = sindex_entity.RowSindex(sheet_info=sf, position=position)
        self._events.append(sindex_events.SindexCreated(entity=sindex))
        return sindex

    async def update_sindex(self, sindex: sindex_entity.Sindex):
        old = await self._repo.get_one_by_uuid(sindex.uuid)
        self._events.append(sindex_events.SindexUpdated(old_entity=old, new_entity=sindex))

    async def delete_sindexes(self, sindexes: list[sindex_entity.Sindex]):
        for sindex in sindexes:
            self._events.append(sindex_events.SindexDeleted(entity=sindex))

    async def reindex_rows(self, sf: sf_entity.SheetInfo):
        rows = await self._repo.get_sheet_rows(sf)
        for i, row in enumerate(rows):
            if row.position != i:
                row.position = i
                await self._repo.update_one(row)
