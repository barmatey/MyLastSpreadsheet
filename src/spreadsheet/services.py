from abc import ABC, abstractmethod
from uuid import UUID

import pandas as pd

from src.core import OrderBy
from src.base import eventbus, broker
from src.base.repo import repository

from . import domain
from . import subscriber

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

    @abstractmethod
    async def get_sheet_size(self, shet_uuid: UUID) -> tuple[int, int]:
        raise NotImplemented


class SheetService:
    def __init__(self, repo: SheetRepository, queue: eventbus.Queue):
        self._repo = repo
        self._queue = queue

    async def create_sheet(self, table: domain.Table = None) -> domain.Sheet:
        if table is None:
            table = []
        size = (len(table), len(table[0])) if len(table) else (0, 0)
        sf = domain.SheetInfo()

        row_sindexes = [
            domain.RowSindex(sf=sf, position=i, size=30, scroll=30 * i)
            for i in range(0, size[0])]

        col_sindexes = [
            domain.ColSindex(sf=sf, position=j, size=120, scroll=120 * j)
            for j in range(0, size[1])]

        cells = []
        for i, row in enumerate(table):
            if len(row) != size[1]:
                raise Exception(f"expected size is {size[1]} but real size is {len(row)}")
            for j, cell_value in enumerate(row):
                cells.append(domain.Cell(sf=sf, row=row_sindexes[i], col=col_sindexes[j], value=cell_value))

        sheet = domain.Sheet(sf=sf, rows=row_sindexes, cols=col_sindexes, cells=cells, size=size)
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

    async def insert_rows_from_position(self, sheet_id: UUID, table: domain.Table, from_pos: int):
        size = await self._repo.get_sheet_size(sheet_id)

        if size != (0, 0):
            filter_by = {"sheet_id": sheet_id, "position.__gte": from_pos}
            rows_after = await self._repo.row_repo.get_many(filter_by=filter_by, order_by=OrderBy("position", asc=True))
            if rows_after:
                for sindex in rows_after:
                    sindex.position = sindex.position + len(table)
                await self._repo.row_repo.update_many(rows_after)

        sf = domain.SheetInfo(id=sheet_id)
        new_rows = [domain.RowSindex(position=from_pos + i, sf=sf, size=30, scroll=(from_pos + i) * 30)
                    for i in range(0, len(table))]
        await self._repo.row_repo.add_many(new_rows)

        if size[1] != 0:
            cols = await self._repo.col_repo.get_many({"sheet_id": sheet_id}, order_by=OrderBy("position", True))
        else:
            cols = [domain.ColSindex(position=j, sf=sf, size=120, scroll=j * 120) for j in range(0, len(table[0]))]
            await self._repo.col_repo.add_many(cols)

        cells = []
        for i, row in enumerate(new_rows):
            for j, col in enumerate(cols):
                cells.append(domain.Cell(sf=sf, row=row, col=col, value=table[i][j]))
        await self._repo.cell_repo.add_many(cells)

    async def insert_sindexes_from_position(self, sheet_id: UUID, table: domain.Table, from_pos: int, axis: int):
        size = await self._repo.get_sheet_size(sheet_id)
        if size == (0, 0):
            raise Exception

        if axis == 0:
            primary_repo = self._repo.row_repo
            secondary_repo = self._repo.col_repo
            sindex_class = domain.RowSindex
        else:
            primary_repo = self._repo.col_repo
            secondary_repo = self._repo.row_repo
            sindex_class = domain.ColSindex

        filter_by = {"sheet_id": sheet_id, "position.__gte": from_pos}
        sindexes_after = await primary_repo.get_many(filter_by=filter_by, order_by=OrderBy("position", asc=True))
        if sindexes_after:
            for sindex in sindexes_after:
                sindex.position = sindex.position + len(table)
            await primary_repo.update_many(sindexes_after)

        sf = domain.SheetInfo(id=sheet_id)
        primary_sindexes = [sindex_class(position=from_pos + i, sf=sf, size=30, scroll=(from_pos + i) * 30)
                            for i in range(0, len(table))]
        await primary_repo.add_many(primary_sindexes)
        secondary_sindexes = await secondary_repo.get_many({"sheet_id": sheet_id}, order_by=OrderBy("position", True))

        cells = []
        for i, primary in enumerate(primary_sindexes):
            for j, secondary in enumerate(secondary_sindexes):
                row, col = (primary, secondary) if axis == 0 else (secondary, primary)
                try:
                    cells.append(domain.Cell(sf=sf, row=row, col=col, value=table[i][j]))
                except IndexError:
                    cells.append(domain.Cell(sf=sf, row=row, col=col, value=None))
        await self._repo.cell_repo.add_many(cells)

    async def delete_sindexes_from_position(self, sheet_id: UUID, from_pos: int, count: int, axis: int):
        repo = self._repo.row_repo if axis == 0 else self._repo.col_repo
        filter_by = {"sheet_id": sheet_id, "position.__gte": from_pos, "position.__lt": from_pos + count}
        sindexes = await repo.get_many(filter_by=filter_by)
        await self.delete_sindexes(sindexes)

    async def insert_sindexes(self, sheet_id: UUID, table: domain.Table, before: domain.Sindex):
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

        await self._repo.cell_repo.remove_many(filter_by={"id.__in": [x.id for x in cells]})
        await repo.remove_many(filter_by={"id.__in": [x.id for x in sindexes]})
        await self._repo.sheet_info_repo.update_one(new_sf)
        await self.reindex(sindexes[0].sf.id, axis)

        for x in sindexes:
            self._queue.append(eventbus.Deleted(key="SindexDeleted", entity=x))

    async def update_cells(self, cells: list[domain.Cell], old_values: list[domain.Cell] = None):
        if old_values is None:
            ids = [x.id for x in cells]
            old_values = await self._repo.cell_repo.get_many_by_id(ids)
        if len(old_values) != len(cells):
            raise Exception(f"{len(old_values)} != {len(cells)}")
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


async def create_rows(sf, start_position: int, count: int) -> list[domain.RowSindex]:
    rows = [domain.RowSindex(position=start_position + i, sf=sf, size=30, scroll=(start_position + i) * 30)
            for i in range(0, count)]
    return rows


async def create_cols(sf, start_position: int, count: int) -> list[domain.ColSindex]:
    cols = [domain.ColSindex(position=j, sf=sf, size=120, scroll=j * 120)
            for j in range(start_position, start_position + count)]
    return cols


async def create_cells_from_table(sf, rows, cols, table) -> list[domain.Cell]:
    cells = []
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            cells.append(domain.Cell(sf=sf, row=row, col=col, value=table[i][j]))
    return cells


class NewSheetService:
    def __init__(self, repo: SheetRepository):
        self._repo = repo

    async def append_rows_from_table(self, sheet_id: UUID, table: domain.Table):
        sf = domain.SheetInfo(id=sheet_id)
        size = await self._repo.get_sheet_size(sheet_id)
        for row in table:
            if len(row) != size[1] and size[1] != 0:
                raise Exception
        rows = await create_rows(sf, start_position=size[0], count=len(table))
        await self._repo.row_repo.add_many(rows)

        if size[1] != 0:
            cols = self._repo.col_repo.get_many({"sheet_id": sheet_id}, OrderBy("position", True))
        else:
            cols = await create_cols(sf, start_position=0, count=len(table[0]))
            await self._repo.col_repo.add_many(cols)
        cells = await create_cells_from_table(sf, rows, cols, table)
        await self._repo.cell_repo.add_many(cells)

    async def group_new_data_with_sheet(self, sheet_id: UUID, table: domain.Table, on: list[int]):
        target = await self._repo.get_sheet_by_id(sheet_id)

        lhs = pd.DataFrame(target.as_table())
        rhs = pd.DataFrame(table)

        new_rows = pd.merge(lhs[on], rhs, how="right", indicator=True)
        new_rows: pd.DataFrame = new_rows.loc[new_rows["_merge"] == "right_only"]

        await self.append_rows_from_table(sheet_id, new_rows.values)


class ExpandCellFollowers:
    def __init__(self, repo: CellRepository, broker_service: broker.BrokerService,
                 subfac: subscriber.SubscriberFactory):
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

                parent_cell = await self._repo.get_sliced_cells(pub.sf.id, parent_row_pos, parent_col_pos)
                await self._subfac.create_cell_subscriber(cell).follow_cells(parent_cell)
