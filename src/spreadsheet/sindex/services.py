from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    subscriber as sindex_subscriber,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
)
from src.spreadsheet.sheet import (
    services as sheet_services,
    repository as sheet_repo,
)


class SindexHandler:
    def __init__(self, repo: sheet_repo.SheetRepo, broker: Broker, queue: Queue):
        self._broker = broker
        self._events = queue
        self._repo = repo

    async def handle_sindex_created(self, event: sindex_events.SindexCreated):
        raise NotImplemented

    async def handle_sindex_updated(self, event: sindex_events.SindexUpdated):
        subs: set[sindex_subscriber.SindexSubscriber] = self._broker.get_subscribers(event.new_entity, self._repo,
                                                                                     self._events)
        for sub in subs:
            await sub.on_sindex_updated(old_value=event.old_entity, new_value=event.new_entity)

    async def handle_sindex_deleted(self, event: sindex_events.SindexDeleted):
        subs: set[sindex_subscriber.SindexSubscriber] = self._broker.get_subscribers(event.entity, self._repo,
                                                                                     self._events)
        for sub in subs:
            await sub.on_sindex_deleted(event.entity)

    async def handle_sindex_subscribed(self, event: sindex_events.SindexSubscribed):
        sub = SindexSelfSubscriber(event.sub, self._repo, self._events)
        await sub.follow_sindexes(event.pubs)
        self._broker.subscribe_to_many(event.pubs, sub)


class SindexService:
    def __init__(self, repo: sheet_repo.SheetRepo, events: Queue):
        self._events = events
        self._repo = repo

    async def create_sindex(self, sindex: sindex_entity.Sindex):
        await self._repo.sindex_repo.add(sindex)

    async def subscribe_sindex(self, pubs, sub: sindex_entity.Sindex):
        self._events.append(sindex_events.SindexSubscribed(pubs=pubs, sub=sub))

    async def create_row(self, sf: sf_entity.SheetInfo, position: int) -> sindex_entity.RowSindex:
        sindex = sindex_entity.RowSindex(sheet_info=sf, position=position)
        await self._repo.sindex_repo.add(sindex)
        return sindex

    async def update_sindex(self, sindex: sindex_entity.Sindex):
        old = await self._repo.sindex_repo.get_one_by_uuid(sindex.uuid)
        await self._repo.sindex_repo.add(sindex)
        self._events.append(sindex_events.SindexUpdated(old_entity=old, new_entity=sindex))

    async def delete_sindexes(self, sindexes: list[sindex_entity.Sindex]):
        await self._repo.sindex_repo.remove_many(sindexes)
        for sindex in sindexes:
            self._events.append(sindex_events.SindexDeleted(entity=sindex))

    async def reindex_rows(self, sf: sf_entity.SheetInfo):
        rows = await self._repo.sindex_repo.get_sheet_rows(sf)
        for i, row in enumerate(rows):
            if row.position != i:
                row.position = i
                await self._repo.sindex_repo.update_one(row)


class SindexSelfSubscriber(sindex_subscriber.SindexSubscriber):
    def __init__(self, entity: sindex_entity.Sindex, repo: sheet_repo.SheetRepo, queue: Queue):
        self._queue = queue
        self._entity = entity
        self._repo = repo

    @property
    def entity(self):
        return self._entity

    async def follow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        pass

    async def unfollow_sindexes(self, pubs: list[sindex_entity.Sindex]):
        pass

    async def on_sindex_updated(self, old_value: sindex_entity.Sindex, new_value: sindex_entity.Sindex):
        pass

    async def on_sindex_deleted(self, pub: sindex_entity.Sindex):
        await sheet_services.SheetService(self._repo, self._queue).delete_sindexes([self._entity])
