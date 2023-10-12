from .. import domain
from .. import subscriber
from .. import services
from ..broker import BrokerService


class CellSelfSubscriber(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Cell, sheet_service: services.SheetService, broker_service: BrokerService):
        self._sheet_service = sheet_service
        self._broker_service = broker_service
        self._entity = entity

    async def follow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = pubs[0].value
        await self._broker_service.subscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_one(self._entity, old)

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        old = self._entity.model_copy(deep=True)
        self._entity.value = None
        await self._broker_service.unsubscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_one(self._entity, old)

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        self._entity.value = actual.value
        await self._sheet_service.cell_service.update_one(old, actual)

    async def on_cell_deleted(self, pub: domain.Cell):
        old = self._entity.model_copy(deep=True)
        self._entity.value = "REF_ERROR"
        await self._sheet_service.cell_service.update_one(self._entity, old)


class SindexSelfSubscriber(subscriber.SindexSubscriber):
    def __init__(self, entity: domain.Sindex, sheet_service: services.SheetService, broker_service: BrokerService):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sindexes(self, pubs: list[domain.Sindex]):
        await self._broker_service.subscribe(pubs, self._entity)

    async def unfollow_sindexes(self, pubs: list[domain.Sindex]):
        raise NotImplemented

    async def on_sindex_updated(self, old_value: domain.Sindex, new_value: domain.Sindex):
        pass

    async def on_sindex_deleted(self, pub: domain.Sindex):
        await self._sheet_service.sindex_service.delete_one(self._entity)


class SheetSelfSubscriber(subscriber.SheetSubscriber):
    def __init__(self, entity: domain.Sheet, sheet_service: services.SheetService, broker_service: BrokerService):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sheet(self, pub: domain.Sheet):
        if self._entity.sheet_info.size != (0, 0):
            raise ValueError

        # Change sheet size
        old = self._entity.sf.model_copy(deep=True)
        self._entity.sf.size = pub.sf.size
        await self._sheet_service.sf_service.update_one(entity=self._entity.sf, old_entity=old)

        # Create table
        rows = [domain.RowSindex(position=x.position, sheet_info=self._entity.sf) for x in pub.rows]
        cols = [domain.ColSindex(position=x.position, sheet_info=self._entity.sf) for x in pub.cols]
        cells = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                value = pub.cells[i * pub.sheet_info.size[1] + j].value
                cells.append(domain.Cell(sheet_info=self._entity.sheet_info, row=row, col=col, value=value))
        await self._sheet_service.sindex_service.create_many(rows)
        await self._sheet_service.sindex_service.create_many(cols)
        await self._sheet_service.cell_service.create_many(cells)

        # Subscribe
        for parent, child in zip(pub.rows, rows):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cols, cols):
            await self._broker_service.subscribe([parent], child)
        for parent, child in zip(pub.cells, cells):
            await self._broker_service.subscribe([parent], child)

    async def unfollow_sheet(self, pub: domain.Sheet):
        raise NotImplemented

    async def on_rows_appended(self, table: list[list[domain.CellValue]]):
        raise NotImplemented

    async def on_sheet_deleted(self):
        raise NotImplemented


class SubFactory(subscriber.SubscriberFactory):
    def __init__(self, sheet_service: services.SheetService, broker_service: BrokerService):
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    def create_cell_subscriber(self, entity: domain.Cell) -> subscriber.CellSubscriber:
        return CellSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sindex_subscriber(self, entity: domain.Sindex) -> subscriber.SindexSubscriber:
        return SindexSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sheet_subscriber(self, entity: domain.Sheet) -> subscriber.SheetSubscriber:
        return SheetSelfSubscriber(entity, self._sheet_service, self._broker_service)
