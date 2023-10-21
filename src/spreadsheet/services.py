from abc import ABC, abstractmethod
from uuid import UUID

from src.core import OrderBy
from . import domain
from . import subscriber
from src.base import eventbus, broker
from ..base.repo import repository

Slice = tuple[int, int] | int


class CellRepository(repository.Repository, ABC):
    @abstractmethod
    async def get_sliced_cells(self, sheet_id: UUID, slice_rows: Slice = None,
                               slice_cols: Slice = None) -> list[domain.Cell]:
        raise NotImplemented

    @abstractmethod
    async def update_cell_by_position(self, sheet_id: UUID, row_pos: int, col_pos: int, data: dict):
        raise NotImplemented


class SheetRepository(ABC):
    @property
    def sheet_info_repo(self) -> repository.Repository[domain.SheetInfo]:
        raise NotImplemented

    @property
    def row_repo(self) -> repository.Repository[domain.RowSindex]:
        raise NotImplemented

    @property
    def col_repo(self) -> repository.Repository[domain.ColSindex]:
        raise NotImplemented

    @property
    def cell_repo(self) -> CellRepository:
        raise NotImplemented

    @abstractmethod
    async def add_sheet(self, sheet: domain.Sheet):
        raise NotImplemented

    @abstractmethod
    async def get_sheet_by_id(self, uuid: UUID) -> domain.Sheet:
        raise NotImplemented


class SheetService:
    def __init__(self, repo: SheetRepository, queue: eventbus.Queue):
        self._repo = repo
        self._queue = queue

    async def create_sheet(self, table: domain.Table = None) -> domain.Sheet:
        if table is None:
            table = []
        size = (len(table), len(table[0])) if len(table) else (0, 0)
        sf = domain.SheetInfo(size=size)

        row_sindexes = [domain.RowSindex(sf=sf, position=i) for i in range(0, size[0])]
        col_sindexes = [domain.ColSindex(sf=sf, position=j) for j in range(0, size[1])]

        cells = []
        for i, row in enumerate(table):
            if len(row) != size[1]:
                raise Exception(f"expected size is {size[1]} but real size is {len(row)}")
            for j, cell_value in enumerate(row):
                cells.append(domain.Cell(sf=sf, row=row_sindexes[i], col=col_sindexes[j], value=cell_value))

        sheet = domain.Sheet(sf=sf, rows=row_sindexes, cols=col_sindexes, cells=cells)
        await self._repo.add_sheet(sheet)
        return sheet

    async def merge(self, parent: domain.Sheet, target: domain.Sheet) -> domain.Sheet:
        if target.sf.size != (0, 0):
            raise Exception
        sf = target.sf.model_copy(deep=True)
        sf.size = parent.sf.size
        await self._repo.sheet_info_repo.update_one(sf)

        # Create  rows
        new_rows = [domain.RowSindex(sf=sf, position=x.position) for x in parent.rows]
        await self._repo.row_repo.add_many(new_rows)

        # Create cols
        new_cols = [domain.ColSindex(sf=sf, position=x.position) for x in parent.cols]
        await self._repo.col_repo.add_many(new_cols)

        # Create cells
        new_cells = []
        for i, row in enumerate(new_rows):
            for j, col in enumerate(new_cols):
                value = parent.cells[i * parent.sf.size[1] + j].value
                new_cells.append(domain.Cell(row=row, col=col, sf=sf, value=value))
        await self._repo.cell_repo.add_many(new_cells)

        return domain.Sheet(sf=sf, rows=new_rows, cols=new_cols, cells=new_cells)

    async def insert_sindexes_from_position(self, sheet_id: UUID, table: domain.Table, from_pos: int, axis: int):
        sf = (await self._repo.sheet_info_repo.get_many({"id": sheet_id})).pop()
        if sf.size == (0, 0):
            raise Exception

        if axis == 0:
            sf.size = (sf.size[0] + len(table), sf.size[1])
            primary_repo = self._repo.row_repo
            secondary_repo = self._repo.col_repo
            sindex_class = domain.RowSindex
        else:
            sf.size = (sf.size[0], sf.size[1] + len(table))
            primary_repo = self._repo.col_repo
            secondary_repo = self._repo.row_repo
            sindex_class = domain.ColSindex
        await self._repo.sheet_info_repo.update_one(sf)

        filter_by = {"sheet_id": sheet_id, "position.__gte": from_pos}
        sindexes_after = await primary_repo.get_many(filter_by=filter_by, order_by=OrderBy("position", asc=True))
        if sindexes_after:
            for sindex in sindexes_after:
                sindex.position = sindex.position + len(table)
            await primary_repo.update_many(sindexes_after)

        primary_sindexes = [sindex_class(position=from_pos + i, sf=sf) for i in range(0, len(table))]
        await primary_repo.add_many(primary_sindexes)
        secondary_sindexes = await secondary_repo.get_many({"sheet_id": sheet_id}, order_by=OrderBy("position", True))

        cells = []
        for i, primary in enumerate(primary_sindexes):
            for j, secondary in enumerate(secondary_sindexes):
                row, col = (primary, secondary) if axis == 0 else (secondary, primary)
                cells.append(domain.Cell(sf=sf, row=row, col=col, value=table[i][j]))
        await self._repo.cell_repo.add_many(cells)

    async def insert_sindexes(self, sheet_id: UUID, table: domain.Table, before: domain.Sindex):
        sf = (await self._repo.sheet_info_repo.get_many({"id": sheet_id})).pop()
        axis = 0 if isinstance(before, domain.RowSindex) else 1
        await self.insert_sindexes_from_position(sheet_id, table, before.position, axis)

    async def delete_sindexes(self, sindexes: list[domain.Sindex], cells: list[domain.Cell] = None):
        """Function changes sheet_info inplace"""

        axis = 0 if isinstance(sindexes[0], domain.RowSindex) else 1
        new_sf = sindexes[0].sf
        if axis == 0:
            key = "row_sindex_id.__in"
            repo = self._repo.row_repo
            new_sf.size = (new_sf.size[0] - len(sindexes), new_sf.size[1])
        else:
            key = "col_sindex_id.__in"
            repo = self._repo.col_repo
            new_sf.size = (new_sf.size[0], new_sf.size[1] - len(sindexes))

        if cells is None:
            ids = [x.id for x in sindexes]
            cells = await self._repo.cell_repo.get_many(filter_by={key: ids})

        await self._repo.cell_repo.remove_many(cells)
        await repo.remove_many(sindexes)
        await self._repo.sheet_info_repo.update_one(new_sf)
        await self.reindex(sindexes[0].sf.id, axis)

        for row in sindexes:
            self._queue.append(eventbus.Deleted(key="SindexDeleted", entity=row))

    async def update_cells(self, cells: list[domain.Cell], old_values: list[domain.Cell] = None):
        if old_values is None:
            ids = [x.id for x in cells]
            old_values = await self._repo.cell_repo.get_many_by_id(ids)
        if len(old_values) != len(cells):
            raise Exception
        for old, actual in zip(old_values, cells):
            await self._repo.cell_repo.update_one(actual)
            self._queue.append(eventbus.Updated(key="CellUpdated", old_entity=old, actual_entity=actual))

    async def reindex(self, sheet_id: UUID, axis=0):
        filter_by = {"sheet_id": sheet_id}
        repo = self._repo.row_repo if axis == 0 else self._repo.col_repo
        sindexes = await repo.get_many(filter_by=filter_by, order_by=OrderBy("position", True))
        to_update = []
        for i, row in enumerate(sindexes):
            if row.position != i:
                row.position = i
                to_update.append(row)
        await repo.update_many(to_update)

    async def get_sheet_by_uuid(self, uuid: UUID) -> domain.Sheet:
        return await self._repo.get_sheet_by_id(uuid)

    async def get_cell_by_index(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.Cell:
        cells = await self._repo.cell_repo.get_sliced_cells(sheet_id, row_pos, col_pos)
        return cells.pop()

    async def update_cell_value_by_index(self, sheet_id: UUID, row_pos: int, col_pos: int, value: domain.CellValue):
        raise NotImplemented


class Handler:
    def __init__(self, sub_factory: subscriber.SubscriberFactory, broker_service: broker.BrokerService):
        self._sub_factory = sub_factory
        self._broker = broker_service


class CellHandler(Handler):
    async def handle_cell_updated(self, event: eventbus.Updated[domain.Cell]):
        subs = [self._sub_factory.create_cell_subscriber(x) for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_cell_updated(old=event.old_entity, actual=event.actual_entity)

    async def handle_cell_deleted(self, event: eventbus.Deleted[domain.Cell]):
        subs = [self._sub_factory.create_cell_subscriber(x) for x in await self._broker.get_subs(event.entity)]
        for sub in subs:
            await sub.on_cell_deleted(pub=event.entity)


class SindexHandler(Handler):
    async def handle_sindex_updated(self, event: eventbus.Updated[domain.Sindex]):
        subs = [self._sub_factory.create_sindex_subscriber(x) for x in await self._broker.get_subs(event.actual_entity)]
        for sub in subs:
            await sub.on_sindex_updated(event.old_entity, event.actual_entity)

    async def handle_sindex_deleted(self, event: eventbus.Deleted[domain.Sindex]):
        subs = [self._sub_factory.create_sindex_subscriber(x) for x in await self._broker.get_subs(event.entity)]
        for sub in subs:
            await sub.on_sindex_deleted(pub=event.entity)


class ExpandCellFollowers:
    def __init__(self, repo: CellRepository, broker_service: broker.BrokerService, subfac: subscriber.SubscriberFactory):
        self._repo = repo
        self._broker = broker_service
        self._subfac = subfac

    async def execute(self, from_cells: list[domain.Cell], to_cells: list[domain.Cell]):
        len_cols = len(from_cells)
        table = [from_cells] + [to_cells[i:i + len_cols] for i in range(0, len(to_cells), len_cols)]

        for i, row in enumerate(table[1:]):
            for j, cell in enumerate(row):
                pubs = await self._broker.get_pubs(table[i][j])
                if len(pubs) != 1:
                    raise Exception
                pub = pubs.pop()
                if not isinstance(pub, domain.Cell):
                    raise Exception
                parent_row_pos, parent_col_pos = pub.row.position + 1, pub.col.position

                parent_cell = await self._repo.get_sliced_cells(pub.sf.id, (parent_row_pos,), (parent_col_pos,))
                await self._subfac.create_cell_subscriber(cell).follow_cells(parent_cell)
