from datetime import datetime
from typing import Sequence, Union, Literal
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field

from src.core import Table


class Sindex(BaseModel):
    position: int
    size: int
    sheet_id: UUID
    is_readonly: bool = False
    is_freeze: bool = False
    id: UUID = Field(default_factory=uuid4)


class RowSindex(Sindex):
    size: int = 30


class ColSindex(Sindex):
    size: int = 120


CellValue = Union[int, float, str, bool, None, datetime]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(BaseModel):
    value: CellValue
    row_id: UUID
    col_id: UUID
    sheet_id: UUID
    background: str = 'white'
    id: UUID = Field(default_factory=uuid4)

    def __repr__(self):
        return f"Cell({self.value})"

    def __str__(self):
        return f"Cell({self.value})"


class SheetInfo(BaseModel):
    title: str
    id: UUID = Field(default_factory=uuid4)


class Sheet(BaseModel):
    sf: SheetInfo
    rows: Sequence[RowSindex]
    cols: Sequence[ColSindex]
    table: Table[Cell]

    @classmethod
    def from_table(cls, table: Table[CellValue], rows: list[RowSindex] = None, cols: list[ColSindex] = None) -> 'Sheet':
        sf = SheetInfo(title="")
        rows = [RowSindex(position=i, sheet_id=sf.id) for i in range(0, len(table))] if rows is None else rows
        cols = [ColSindex(position=j, sheet_id=sf.id) for j in range(0, len(table[0]))] if cols is None else cols
        cells = []
        for i, row in enumerate(table):
            cells.append([Cell(value=value, row_id=rows[i].id, col_id=cols[j].id, sheet_id=sf.id)
                          for j, value in enumerate(row)])
        if len(rows) != len(table):
            raise Exception
        return cls(sf=sf, rows=rows, cols=cols, table=cells)

    def drop(self, ids: Sequence[UUID] | UUID, axis: int, reindex=True, inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        ids = {ids} if isinstance(ids, UUID) else set(ids)
        row_ids = [x.id for x in target.rows]
        col_ids = [x.id for x in target.cols]

        new_table = pd.DataFrame(target.table, index=row_ids, columns=col_ids).drop(ids, axis=axis).values
        if axis == 0:
            new_rows = list(filter(lambda x: x.id not in ids, target.rows))
            new_cols = target.cols
        elif axis == 1:
            new_rows = target.rows
            new_cols = list(filter(lambda x: x.id not in ids, target.cols))
        else:
            raise Exception
        target.rows = new_rows
        target.cols = new_cols
        target.table = new_table
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

    def drop_old(self, ids: Sequence[UUID], axis: int, reindex=True, inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        ids = set(ids)
        if axis == 0:
            new_rows: list[RowSindex] = []
            new_table: Table[Cell] = []
            for i, row in enumerate(self.rows):
                if row.id in ids:
                    new_rows.append(row)
                    new_table.append(self.table[i])
            target.rows = new_rows
            target.table = new_table
        elif axis == 1:
            new_cols: list[ColSindex] = []
            new_table: Table[Cell] = [[] for _x in range(0, len(target.table))]
            for j, col in enumerate(self.cols):
                if col.id in ids:
                    new_cols.append(col)
                    for row in target.table:
                        pass

    def to_simple_frame(self) -> pd.DataFrame:
        index = [x.id for x in self.rows]
        columns = [x.id for x in self.cols]
        data = map(lambda row: map(lambda cell: cell.value, row), self.table)
        df = pd.DataFrame(data, index, columns)
        return df
