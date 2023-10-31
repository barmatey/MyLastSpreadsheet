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
        return f"{self.__class__.__name__}(position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position})"


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
    row: RowSindex
    col: ColSindex
    background: str = 'white'
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"Cell(index=({self.row.position}, {self.col.position}), value={self.value})"

    def __repr__(self):
        return f"Cell(index=({self.row.position}, {self.col.position}), value={self.value})"

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other: 'Cell'):
        return self.value == other.value

    def __add__(self, other: 'Cell'):
        cell = Cell(row=self.row.model_copy(), col=self.col.model_copy(), background=self.background,
                    value=self.value + other.value)
        return cell


class Sheet:
    def __init__(self, data: Table[Cell] = None, rows: list[RowSindex] = None, cols: list[ColSindex] = None,
                 dtype=None, copy=None):
        self._rows: dict[UUID, RowSindex] = {}
        self._cols: dict[UUID, ColSindex] = {}

        index = []
        for row in rows:
            index.append(row.id)
            self._rows[row.id] = row.model_copy(deep=True)

        columns = []
        for col in cols:
            columns.append(col.id)
            self._cols[col.id] = col.model_copy(deep=True)

        self._frame = pd.DataFrame(data, index=index, columns=columns, dtype=dtype, copy=copy)

    @property
    def frame(self):
        return self._frame

    @property
    def row_dict(self):
        return self._rows

    @property
    def col_dict(self):
        return self._cols

    @property
    def rows(self):
        return [self._rows[x] for x in self._frame.index]

    @property
    def cols(self):
        return [self._cols[x] for x in self._frame.columns]

    def __str__(self):
        index = [self._rows[x] for x in self._frame.index]
        columns = [self._cols[x] for x in self._frame.columns]
        df = pd.DataFrame(self._frame.values, index=index, columns=columns)
        return str(df)

    def __repr__(self):
        raise NotImplemented

    def __add__(self, other: 'Sheet'):
        sheet = self.copy()
        sheet._frame = sheet._frame + other._frame
        sheet._rows = sheet._rows | other._rows
        sheet._cols = sheet._cols | other._cols
        return sheet

    @classmethod
    def from_table(cls, table: Table[CellValue]):
        rows = [RowSindex(position=i) for i in range(0, len(table))]
        cols = [ColSindex(position=j) for j in range(0, len(table[0]))]
        cells = []
        for i, row in enumerate(table):
            cells.append([Cell(value=value, row=rows[i], col=cols[j]) for j, value in enumerate(row)])
        return cls(cells, rows, cols)

    def drop(self,
             labels: Hashable | Sequence[Hashable] | None = None,
             axis: Literal["index", "columns", "rows"] | int = 0,
             level: Hashable | None = None,
             errors: Literal["ignore", "raise"] = "raise",
             reindex=True) -> 'Sheet':
        if isinstance(labels, Hashable):
            labels = [labels]
        self._frame = self._frame.drop(labels, axis=axis, level=level, errors=errors)
        if axis == 0:
            for item in labels:
                del self._rows[item]
            if reindex:
                self.reindex_rows()
        else:
            for item in labels:
                del self._cols[item]
            if reindex:
                self.reindex_cols()
        return self

    def reindex_rows(self):
        for i, row_id in enumerate(self._frame.index):
            self._rows[row_id].position = i
        return self

    def reindex_cols(self):
        for j, col_id in enumerate(self._frame.columns):
            self._cols[col_id].position = j
        return self

    def copy(self) -> 'Sheet':
        return deepcopy(self)

    def to_table(self) -> Table[CellValue]:
        result = []
        for row in self._frame.values:
            result.append([x.value for x in row])
        return result
