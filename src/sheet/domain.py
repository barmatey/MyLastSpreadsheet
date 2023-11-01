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
                 dtype=None, copy=None, sheet_id: UUID = None):
        self.id = sheet_id if sheet_id is not None else uuid4()

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


