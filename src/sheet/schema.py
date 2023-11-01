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
    rows: list[RowSindex]
    cols: list[ColSindex]
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

        target.table = pd.DataFrame(target.table, index=row_ids, columns=col_ids).drop(ids, axis=axis).values
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
                cells = [Cell(value=None, row_id=row.id, col_id=col.id, sheet_id=target.sf.id) for col in target.cols]
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
                    target.table[i].append(Cell(value=None, row_id=row.id, col_id=col.id, sheet_id=target.sf.id))
        return target

    def replace_cell_values(self, table: Table[CellValue], inplace=False) -> 'Sheet':
        target = self if inplace else self.model_copy(deep=True)
        if len(table) != len(target.table):
            raise Exception
        for i, row in enumerate(table):
            if len(row) != len(target.rows):
                raise Exception
            for j, value in enumerate(row):
                target.table[i][j].value = value
        return target

    def to_simple_frame(self) -> pd.DataFrame:
        index = [x.id for x in self.rows]
        columns = [x.id for x in self.cols]
        data = map(lambda row: map(lambda cell: cell.value, row), self.table)
        df = pd.DataFrame(data, index, columns)
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
        target.table = pd.concat([pd.DataFrame(lhs.table), pd.DataFrame(rhs.table)], axis=1).values
    else:
        raise Exception

    if reindex:
        target.reindex(axis, inplace=True)

    return target

