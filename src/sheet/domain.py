from copy import deepcopy
from datetime import datetime
from typing import Literal, Union, Hashable, Sequence
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field

from src.core import Table


class Sindex(BaseModel):
    position: int
    size: int
    scroll: int | None = None
    is_readonly: bool = False
    is_freeze: bool = False
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.__class__.__name__.split('Sindex')[0]}({self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__.split('Sindex')[0]}({self.position})"


class RowSindex(Sindex):
    size: int = 30

    def __hash__(self):
        return self.id.__hash__()


class ColSindex(Sindex):
    size: int = 120

    def __hash__(self):
        return self.id.__hash__()


CellValue = Union[int, float, str, bool, None, datetime]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(BaseModel):
    value: CellValue
    row_id: UUID
    col_id: UUID
    background: str = 'white'
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"Cell(value={self.value})"

    def __repr__(self):
        return f"Cell(value={self.value})"

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other: 'Cell'):
        return self.value == other.value

    def __add__(self, other: 'Cell'):
        cell = Cell(row_id=self.id, col_id=self.col_id, background=self.background, value=self.value + other.value)
        return cell


class Sheet:
    def __init__(self, data: Table[Cell] = None, rows: list[RowSindex] = None, cols: list[ColSindex] = None,
                 dtype=None, copy=None):
        self._row_dict: dict[UUID, RowSindex] = {}
        self._col_dict: dict[UUID, ColSindex] = {}

        index = []
        for row in rows:
            index.append(row.id)
            self._row_dict[row.id] = row.model_copy(deep=True)

        columns = []
        for col in cols:
            columns.append(col.id)
            self._col_dict[col.id] = col.model_copy(deep=True)

        self._frame = pd.DataFrame(deepcopy(data), index=index, columns=columns, dtype=dtype, copy=copy)

    @property
    def frame(self):
        return self._frame

    @property
    def row_dict(self):
        return self._row_dict

    @property
    def col_dict(self):
        return self._col_dict

    @property
    def rows(self):
        return [self._row_dict[x] for x in self._frame.index]

    @property
    def cols(self):
        return [self._col_dict[x] for x in self._frame.columns]

    def __str__(self):
        df = pd.DataFrame(self._frame.values, index=self.rows, columns=self.cols).to_string()
        return df

    def __repr__(self):
        raise NotImplemented

    def __add__(self, other: 'Sheet'):
        sheet = self.copy()
        sheet._frame = sheet._frame + other._frame
        sheet._row_dict = sheet._row_dict | other._row_dict
        sheet._col_dict = sheet._col_dict | other._col_dict
        return sheet

    @classmethod
    def from_table(cls, table: Table[CellValue], rows: list[RowSindex] = None, cols: list[ColSindex] = None):
        rows = [RowSindex(position=i) for i in range(0, len(table))] if rows is None else rows
        cols = [ColSindex(position=j) for j in range(0, len(table[0]))] if cols is None else cols
        cells = []
        for i, row in enumerate(table):
            cells.append([Cell(value=value, row_id=rows[i].id, col_id=cols[j].id) for j, value in enumerate(row)])
        if len(rows) != len(table):
            raise Exception
        return cls(cells, rows, cols)

    def drop(self,
             labels: Hashable | Sequence[Hashable] | None = None,
             axis: Literal["index", "columns", "rows"] | int = 0,
             level: Hashable | None = None,
             errors: Literal["ignore", "raise"] = "raise",
             reindex=True,
             inplace=False) -> 'Sheet':
        if isinstance(labels, Hashable):
            labels = [labels]

        target = self if inplace else self.copy()
        target._frame = target._frame.drop(labels, axis=axis, level=level, errors=errors)
        if axis == 0:
            for item in labels:
                del target._row_dict[item]
            if reindex:
                target.reindex_rows()
        else:
            for item in labels:
                del target._col_dict[item]
            if reindex:
                target.reindex_cols()
        return target

    def resize_sheet(self, row_count: int = None, col_count: int = None, inplace=False) -> 'Sheet':
        target = self if inplace else self.copy()
        if row_count is None:
            row_count = len(target.frame.index)
        if col_count is None:
            col_count = len(target.frame.columns)

        if len(target._frame.index) >= row_count:
            rows_to_delete = target._frame.index[row_count:]
            target.drop(rows_to_delete, axis=0, inplace=True, reindex=False)
        else:
            for i in range(len(target._frame.index), row_count):
                row = RowSindex(position=i)
                cells = [Cell(value=None, row_id=row.id, col_id=col_id) for col_id in target.frame.columns]
                target._row_dict[row.id] = row
                target._frame.loc[row.id] = cells

        if len(target._frame.columns) >= col_count:
            cols_to_delete = target._frame.columns[col_count:]
            target.drop(cols_to_delete, axis=1, inplace=True, reindex=False)
        else:
            for j in range(len(target._frame.columns), col_count):
                col = ColSindex(position=j)
                cells = [Cell(value=None, row_id=row_id, col_id=col.id) for row_id in target._frame.index]
                target._col_dict[col.id] = col
                target._frame[col.id] = cells

        return target

    def replace_cell_values(self, table: Table[CellValue], inplace=False) -> 'Sheet':
        target = self if inplace else self.copy()
        if len(table) != target._frame.shape[0]:
            raise Exception
        for i, row in enumerate(table):
            if len(row) != target._frame.shape[1]:
                raise Exception
            for j, cell_value in enumerate(row):
                target._frame.iloc[i, j].value = cell_value
        return target

    def concat(self, other: 'Sheet', axis=0, inplace=False) -> 'Sheet':
        target = self if inplace else self.copy()
        if axis == 0:
            if target._frame.shape[1] != other._frame.shape[1]:
                raise Exception
            for lhs, rhs in zip(target._frame.columns, other._frame.columns):
                if lhs != rhs:
                    raise Exception
            if len(target._row_dict | other._row_dict) != len(target.row_dict) + len(other._row_dict):
                raise Exception
            target._row_dict = target._row_dict | other.row_dict
            target._frame = pd.concat([target._frame, other._frame])
            target.reindex_rows()
        elif axis == 1:
            if target._frame.shape[0] != other._frame.shape[0]:
                raise Exception
            for lhs, rhs in zip(target._frame.index, other._frame.index):
                if lhs != rhs:
                    raise Exception
            if len(target._col_dict | other._col_dict) != len(target._col_dict) + len(other._col_dict):
                raise Exception
            target._col_dict = target._col_dict | other._col_dict
            target._frame = pd.concat([target._frame, other._frame], axis=1)
            target.reindex_cols()
        else:
            raise ValueError
        return target

    def reindex_rows(self):
        for i, row_id in enumerate(self._frame.index):
            self._row_dict[row_id].position = i

    def reindex_cols(self):
        for j, col_id in enumerate(self._frame.columns):
            self._col_dict[col_id].position = j

    def copy(self) -> 'Sheet':
        cells = self._frame.values
        rows = self.rows
        cols = self.cols
        return self.__class__(cells, rows, cols)

    def to_table(self) -> Table[CellValue]:
        result = []
        for row in self._frame.values:
            result.append([x.value for x in row])
        return result

    def to_simple_frame(self) -> pd.DataFrame:
        df = self._frame.apply(lambda x: x.apply(lambda y: y.value))
        return df


class SheetDifference:
    def __init__(self, old_sheet: Sheet, new_sheet: Sheet):
        self._old_sheet = old_sheet
        self._new_sheet = new_sheet

        self.appended_rows: set[RowSindex] = set()
        self.deleted_rows: set[RowSindex] = set()
        self.moved_rows: set[RowSindex] = set()

        self.appended_cols: set[ColSindex] = set()
        self.deleted_cols: set[ColSindex] = set()
        self.moved_cols: set[ColSindex] = set()

        self.deleted_cells: set[Cell] = set()
        self.appended_cells: set[Cell] = set()
        self.updated_cells: set[Cell] = set()

    def find_updated_cells(self):
        common_rows = list(set(self._old_sheet.row_dict.keys()).intersection(self._new_sheet.row_dict.keys()))
        common_cols = list(set(self._old_sheet.col_dict.keys()).intersection(self._new_sheet.col_dict.keys()))
        old = self._old_sheet.frame.loc[common_rows, common_cols]
        new = self._new_sheet.frame.loc[common_rows, common_cols]
        diff: pd.DataFrame = old.compare(new, align_axis=0)
        for col in diff.columns:
            temp = diff[col].dropna()
            for i in range(0, len(temp), 2):
                self.updated_cells.add(temp[i + 1])

    def find_moved_rows(self):
        for key, new_value in self._new_sheet.row_dict.items():
            old_value = self._old_sheet.row_dict.get(key)
            if old_value:
                if old_value.position != new_value.position:
                    self.moved_rows.add(new_value)

    def find_moved_cols(self):
        for key, new_value in self._new_sheet.col_dict.items():
            old_value = self._old_sheet.col_dict.get(key)
            if old_value:
                if old_value.position != new_value.position:
                    self.moved_cols.add(new_value)

    def find_appended_rows(self):
        appended = {
            key: value
            for key, value in self._new_sheet.row_dict.items()
            if self._old_sheet.row_dict.get(key) is None
        }
        self.appended_rows = self.appended_rows.union(appended.values())
        self.appended_cells = self.appended_cells.union(
            self._new_sheet.frame.filter(appended.keys(), axis=0).values.flatten().tolist()
        )

    def find_appended_cols(self):
        appended = {
            key: value
            for key, value in self._new_sheet.col_dict.items()
            if self._old_sheet.col_dict.get(key) is None
        }
        self.appended_cols = self.appended_cols.union(appended.values())
        self.appended_cells = self.appended_cells.union(
            self._new_sheet.frame.filter(appended.keys(), axis=1).values.flatten().tolist()
        )

    def find_deleted_rows(self):
        deleted = {
            key: value
            for key, value in self._old_sheet.row_dict.items()
            if self._new_sheet.row_dict.get(key) is None
        }
        self.deleted_rows = self.deleted_rows.union(deleted.values())
        self.deleted_cells = self.deleted_cells.union(
            self._old_sheet.frame.filter(deleted.keys(), axis=0).values.flatten().tolist())

    def find_deleted_cols(self):
        deleted = {
            key: value
            for key, value in self._old_sheet.col_dict.items()
            if self._new_sheet.col_dict.get(key) is None
        }
        self.deleted_cols = self.deleted_cols.union(deleted.values())
        self.deleted_cells = self.deleted_cells.union(
            self._old_sheet.frame.filter(deleted.keys(), axis=1).values.flatten().tolist()
        )

    def find_updates(self):
        self.find_appended_rows()
        self.find_deleted_rows()
        self.find_moved_rows()

        self.find_appended_cols()
        self.find_deleted_cols()
        self.find_moved_cols()

        self.find_updated_cells()


class ComplexMerge:
    def __init__(self, target_sheet: Sheet, from_sheet: Sheet):
        self._target = target_sheet
        self._from = from_sheet
        self._merged_df = None

    def merge(self, target_on, from_on) -> 'ComplexMerge':
        names = [f"lvl{x+1}" for x in range(0, len(target_on))]

        target_df = self._target.to_simple_frame()
        target_df = target_df.set_index(target_on)
        target_df.index = target_df.index.set_names(names)
        target_df.columns = target_df.iloc[0]
        target_df = target_df.iloc[1:]

        from_df = self._from.to_simple_frame()
        from_df = from_df.set_index(from_on)
        from_df.index = from_df.index.set_names(names)
        from_df.columns = from_df.iloc[0]
        from_df = from_df.iloc[1:]

        self._merged_df = pd.concat([target_df, from_df]).fillna(0).groupby(names).sum()
        return self

    def to_table(self) -> Table:
        df = self._merged_df.reset_index()
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
