from abc import ABC, abstractmethod
from uuid import UUID, uuid4

import pandas as pd

from src.core import OrderBy, Table
from src.base import eventbus, broker
from src.base.repo import repository

from . import domain
from . import subscriber





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


class NewSheetService:
    def __init__(self, repo: SheetRepository):
        self._repo = repo

    async def append_rows_from_sheet(self, target_sheet_id: UUID, sheet: domain.Sheet):
        target_size = await self._repo.get_sheet_size(target_sheet_id)
        target_sf = domain.SheetInfo(id=target_sheet_id)

        if target_size[1] != sheet.size[1] and target_size != (0, 0):
            raise Exception(f"{target_size[1]} != {sheet.size[1]}")

        if target_size[1] != 0:
            cols = await self._repo.col_repo.get_many({"sheet_id": target_sheet_id}, OrderBy("position", True))
        else:
            cols = [domain.ColSindex(
                sf=target_sf,
                position=x.position,
                size=x.size,
                is_freeze=x.is_freeze,
                is_readonly=x.is_readonly,
            ) for x in sheet.cols]
            await self._repo.col_repo.add_many(cols)

        new_rows = []
        new_cells = []
        for i, row in enumerate(sheet.rows):
            row = row.model_copy()
            row.id = uuid4()
            row.position = i + target_size[0]
            row.scroll = None
            row.sf = target_sf
            new_rows.append(row)
            for j, col in enumerate(cols):
                index = i * sheet.size[1] + j
                cell = sheet.cells[index].model_copy()
                cell.id = uuid4()
                cell.row = row
                cell.col = col
                cell.sf = target_sf
                new_cells.append(cell)
        await self._repo.row_repo.add_many(new_rows)
        await self._repo.cell_repo.add_many(new_cells)

    async def merge_sheets(self, sheet1: domain.Sheet, sheet2: domain.Sheet, merge_on: list[domain.ColSindex]):
        sheet1_df = sheet1.to_full_frame()
        sheet2_df = sheet2.to_full_frame()
        merged = pd.concat([sheet1_df, sheet2_df])
        print()
        print(merged.to_string())
        raise NotImplemented

    async def merge_sheets_old(self, target_sheet_id: UUID, data: domain.Sheet, merge_on: list[int]) -> None:
        target_sheet = await self._repo.get_sheet_by_id(target_sheet_id)
        target_frame = target_sheet.to_frame()
        from_frame = data.to_frame()

        on = []
        for j in merge_on:
            if target_frame.iloc[0, j] != from_frame.iloc[0, j]:
                raise ValueError
            on.append(target_frame.iloc[0, j])

        target_frame.columns = target_frame.iloc[0]
        target_frame = target_frame.drop(target_frame.index[0]).reset_index(drop=True)

        from_frame.columns = from_frame.iloc[0]
        from_frame = from_frame.drop(from_frame.index[0]).reset_index(drop=True)

        new_frame = pd.concat([target_frame, from_frame]).fillna(0).groupby(on, sort=False, ).sum().reset_index()
        new_rows = new_frame.iloc[len(target_frame.index):, :len(target_frame.columns)]

        if not new_rows.empty:
            sheet = domain.Sheet.from_table(new_rows.values)
            for j in range(0, len(merge_on)):
                sheet.cols[j].is_freeze = True
            for x in range(0, len(sheet.cells)):
                if sheet.cells[x].row.is_freeze or sheet.cells[x].col.is_freeze:
                    sheet.cells[x].background = "#F8FAFDFF"
            await self.append_rows_from_sheet(target_sheet_id, sheet)

        new_cols = new_frame.iloc[:, len(target_frame.columns):]
        if not new_cols.empty:
            raise NotImplemented

        updated_df = target_frame.compare(
            new_frame.iloc[0:len(target_frame.index), 0:len(target_frame.columns)], align_axis=0)

        cells_to_update: list[domain.Cell] = []
        columns = list(target_frame.columns)
        for col in updated_df.columns:
            temp = updated_df[col].dropna()
            col_pos = columns.index(col)
            for i in range(0, len(temp.index), 2):
                row_pos = temp.index[i][0] + 1  # Add 1 because first row of table is index_col
                old_cell = target_sheet.cells[row_pos * target_sheet.size[1] + col_pos]
                new_cell = old_cell.model_copy(deep=True)
                new_cell.value = temp.iloc[i + 1]
                cells_to_update.append(new_cell)
        await self._repo.cell_repo.update_many(cells_to_update)

    async def sort_sheet(self, sheet: domain.Sheet, order: OrderBy):
        """Sort sheet by cols inplace"""
        df = sheet.to_full_frame()
        df = df.sort_values(order.fields, ascending=order.asc, key=lambda x: x.apply(lambda y: y.value))
        rows_to_update = []
        for i, row in enumerate(df.index):
            if row.position != i:
                row.position = i
                rows_to_update.append(row)
        sheet.rows = list(df.index)
        sheet.cells = df.values.flatten()
        await self._repo.row_repo.update_many(rows_to_update)


class ExpandCellFollowers:
    def __init__(self, repo: CellRepository, broker_service: broker.Broker,
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
