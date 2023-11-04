from abc import abstractmethod
from datetime import datetime
from typing import Sequence, Union, Literal, Any, Iterable
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field

from src.core import Table
from src.helpers.arrays import flatten


class Sindex(BaseModel):
    position: int
    size: int
    sheet_id: UUID
    is_readonly: bool = False
    is_freeze: bool = False
    id: UUID = Field(default_factory=uuid4)

    def __eq__(self, other: 'Sindex'):
        if self.id != other.id:
            raise Exception
        return self.model_dump() == other.model_dump()


class RowSindex(Sindex):
    size: int = 30


class ColSindex(Sindex):
    size: int = 120


CellValue = Union[int, float, str, bool, None, datetime]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(BaseModel):
    value: CellValue
    row: RowSindex
    col: ColSindex
    sheet_id: UUID
    background: str = 'white'
    id: UUID = Field(default_factory=uuid4)

    def __repr__(self):
        return f"Cell({self.value})"

    def __str__(self):
        return f"Cell({self.value})"

    def __eq__(self, other: 'Cell'):
        if self.id != other.id:
            raise Exception
        return self.value == other.value


class Formula(BaseModel):
    cell_id: UUID

    @property
    def value(self):
        raise NotImplemented

    @abstractmethod
    def to_json(self):
        raise NotImplemented


class Sum(Formula):
    _value: Union[int, float] = 0
    id: UUID = Field(default_factory=uuid4)

    def to_json(self):
        return {"id": str(self.id), "value": self.value, }

    @property
    def value(self):
        return self._value

    async def follow_cells(self, pubs: list[Cell]):
        for cell in pubs:
            self._value += cell.value

    async def on_cell_updated(self, old: Cell, actual: Cell):
        self._value = self._value - old.value + actual.value


class Sub(Formula):
    value: Union[int, float] = 0
    id: UUID = Field(default_factory=uuid4)

    def to_json(self):
        return {
            "id": str(self.id),
            "minuend": {str(key): value for key, value in self.minuend.items()},
            "subtrahend": {str(key): value for key, value in self.subtrahend.items()},
        }


class SheetInfo(BaseModel):
    title: str
    id: UUID = Field(default_factory=uuid4)


class Sheet(BaseModel):
    sf: SheetInfo
    rows: list[RowSindex] = Field(default_factory=list)
    cols: list[ColSindex] = Field(default_factory=list)
    table: Table[Cell] = Field(default_factory=list)

    def __init__(self, **data: Any):
        super().__init__(**data)
        if len(self.rows) != len(self.table):
            raise ValueError(f" {len(self.rows)} != {len(self.table)}")
        if len(self.table) and len(self.table[0]) != len(self.cols):
            raise ValueError(f"{len(self.table[0])} != {len(self.cols)}")

    @classmethod
    def from_table(cls, table: Table[CellValue], rows: list[RowSindex] = None, cols: list[ColSindex] = None,
                   freeze_rows: int = 0, freeze_cols: int = 0) -> 'Sheet':
        sf = SheetInfo(title="")
        rows = [RowSindex(position=i, sheet_id=sf.id) for i in range(0, len(table))] if rows is None else rows
        for i in range(0, freeze_rows):
            rows[i].is_freeze = True

        cols = [ColSindex(position=j, sheet_id=sf.id) for j in range(0, len(table[0]))] if cols is None else cols
        for j in range(0, freeze_cols):
            cols[j].is_freeze = True

        cells = []
        for i, row in enumerate(table):
            cells.append([Cell(value=value, row=rows[i], col=cols[j], sheet_id=sf.id)
                          for j, value in enumerate(row)])
        if len(rows) != len(table):
            raise Exception
        return cls(sf=sf, rows=rows, cols=cols, table=cells)

    @property
    def size(self) -> tuple[int, int]:
        return len(self.rows), len(self.cols)

    @property
    def cells(self) -> list[Cell]:
        return flatten(self.table)

    def drop(self, ids: Sequence[UUID] | UUID, axis: int, reindex=True, inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        ids = {ids} if isinstance(ids, UUID) else set(ids)
        row_ids = [x.id for x in target.rows]
        col_ids = [x.id for x in target.cols]

        target.table = pd.DataFrame(target.table, index=row_ids, columns=col_ids).drop(ids, axis=axis).values.tolist()
        if axis == 0:
            target.rows = list(filter(lambda x: x.id not in ids, target.rows))
        elif axis == 1:
            target.cols = list(filter(lambda x: x.id not in ids, target.cols))
        else:
            raise Exception
        if reindex:
            target.reindex(axis, inplace=True)
        return target

    def reindex(self, axis: int, inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        if axis == 0:
            for i, row in enumerate(target.rows):
                row.position = i
        elif axis == 1:
            for j, col in enumerate(target.cols):
                col.position = j
        else:
            raise Exception
        return target

    def resize(self, row_size: int = None, col_size: int = None, inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        if row_size is None:
            row_size = len(target.frame.index)
        if col_size is None:
            col_size = len(target.frame.columns)

        if len(target.rows) >= row_size:
            rows_to_delete = [x.id for x in target.rows[row_size:]]
            target.drop(rows_to_delete, axis=0, inplace=True, reindex=False)
        else:
            for i in range(len(target.rows), row_size):
                row = RowSindex(position=i, sheet_id=target.sf.id)
                cells = [Cell(value=None, row=row, col=col, sheet_id=target.sf.id) for col in target.cols]
                target.rows.append(row)
                target.table.append(cells)

        if len(target.cols) >= col_size:
            cols_to_delete = [x.id for x in target.cols[col_size:]]
            target.drop(cols_to_delete, axis=1, inplace=True, reindex=False)
        else:
            for j in range(len(target.cols), col_size):
                col = ColSindex(position=j, sheet_id=target.sf.id)
                target.cols.append(col)
                for i, row in enumerate(target.rows):
                    target.table[i].append(Cell(value=None, row=row, col=col, sheet_id=target.sf.id))
        return target

    def replace_cell_values(self, table: Table[CellValue], inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        if len(table) != len(target.table):
            raise Exception
        for i, row in enumerate(table):
            if len(row) != len(target.cols):
                raise Exception(f"{len(row)} != {len(target.cols)}")
            for j, value in enumerate(row):
                target.table[i][j].value = value
        return target

    def to_simple_frame(self, index_key="id") -> pd.DataFrame:
        index = [x.__getattribute__(index_key) for x in self.rows]
        columns = [x.__getattribute__(index_key) for x in self.cols]
        data = map(lambda row: map(lambda cell: cell.value, row), self.table)
        df = pd.DataFrame(data, index, columns)
        return df

    def to_full_frame(self) -> pd.DataFrame:
        index = [x.id for x in self.rows]
        columns = [x.id for x in self.cols]
        df = pd.DataFrame(self.table, index, columns)
        return df


def concat(lhs: Sheet, rhs: Sheet, axis=0, reindex=True) -> Sheet:
    lhs = lhs.model_copy(deep=True)
    rhs = rhs.model_copy(deep=True)

    target = lhs
    if axis == 0:
        if len(lhs.cols) != len(rhs.cols):
            raise Exception
        target.rows.extend(rhs.rows)
        target.table.extend(rhs.table)
    elif axis == 1:
        if len(lhs.rows) != len(rhs.rows):
            raise Exception
        target.cols.extend(rhs.cols)
        target.table = pd.concat([pd.DataFrame(lhs.table), pd.DataFrame(rhs.table)], axis=1).values.tolist()
    else:
        raise Exception
    if reindex:
        target.reindex(axis, inplace=True)
    return target


def complex_merge(lhs: Sheet, rhs: Sheet, left_on: list[UUID], right_on: list[UUID], sort=False) -> Table[CellValue]:
    names = [f"lvl{x + 1}" for x in range(0, len(left_on))]

    lhs = lhs.to_simple_frame()
    lhs = lhs.set_index(left_on)
    lhs.index = lhs.index.set_names(names)
    lhs.columns = lhs.iloc[0]
    lhs = lhs.iloc[1:]

    rhs = rhs.to_simple_frame()
    rhs = rhs.set_index(right_on)
    rhs.index = rhs.index.set_names(names)
    rhs.columns = rhs.iloc[0]
    rhs = rhs.iloc[1:]

    df = pd.concat([lhs, rhs]).fillna(0).groupby(names, sort=sort).sum().reset_index()
    # From frame to table
    result = []
    first_row = []
    for col in df.columns:
        if isinstance(col, pd.Timestamp):
            first_row.append(
                datetime(col.year, col.month, col.day, col.hour, col.minute, col.second, tzinfo=col.tzinfo)
            )
        else:
            first_row.append(None)
    result.append(first_row)
    result.extend(df.values.tolist())
    return result


class SheetDifference(BaseModel):
    rows_created: list[RowSindex] = Field(default_factory=list)
    rows_updated: list[RowSindex] = Field(default_factory=list)
    rows_deleted: list[RowSindex] = Field(default_factory=list)
    cols_created: list[ColSindex] = Field(default_factory=list)
    cols_updated: list[ColSindex] = Field(default_factory=list)
    cols_deleted: list[ColSindex] = Field(default_factory=list)
    cells_created: list[Cell] = Field(default_factory=list)
    cells_updated: list[Cell] = Field(default_factory=list)
    cells_deleted: list[Cell] = Field(default_factory=list)

    @classmethod
    def from_sheets(cls, old: Sheet, actual: Sheet):
        old_rows = {x.id: x for x in old.rows}
        actual_rows = {x.id: x for x in actual.rows}

        old_cols = {x.id: x for x in old.cols}
        actual_cols = {x.id: x for x in actual.cols}

        old_cells = {x.id: x for x in flatten(old.table)}
        actual_cells = {x.id: x for x in flatten(actual.table)}

        rows_created, rows_updated, rows_deleted = cls.compare_data(old_rows, actual_rows)
        cols_created, cols_updated, cols_deleted = cls.compare_data(old_cols, actual_cols)
        cells_created, cells_updated, cells_deleted = cls.compare_data(old_cells, actual_cells)
        data = {
            "rows_created": rows_created,
            "rows_updated": rows_updated,
            "rows_deleted": rows_deleted,
            "cols_created": cols_created,
            "cols_updated": cols_updated,
            "cols_deleted": cols_deleted,
            "cells_created": cells_created,
            "cells_updated": cells_updated,
            "cells_deleted": cells_deleted,
        }

        return cls(**data)

    @classmethod
    def compare_data(cls, old: dict, actual: dict) -> tuple[list[Sindex], list[Sindex], list[Sindex]]:
        """Return created, updated, deleted"""
        created = []
        updated = []
        deleted = []
        for actual_id, actual_value in actual.items():
            old_value = old.get(actual_id)
            if old_value is None:
                created.append(actual_value)
            elif old_value != actual_value:
                updated.append(actual_value)

        for old_id, old_value in old.items():
            if actual.get(old_id) is None:
                deleted.append(old_value)

        return created, updated, deleted
