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
        return f"{self.__class__.__name__}({self.id}, position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, position={self.position})"


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
             reindex=True) -> 'Sheet':
        if isinstance(labels, Hashable):
            labels = [labels]

        target = self.copy()
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

    def concat(self, other: 'Sheet', axis=0) -> 'Sheet':
        target = self.copy()
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
