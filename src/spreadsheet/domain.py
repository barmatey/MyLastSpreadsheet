from typing import Union, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.base import eventbus, entity


class SheetInfo(entity.Entity):
    id: UUID = Field(default_factory=uuid4)
    size: tuple[int, int]

    def __str__(self):
        return f"{self.size}"

    def __repr__(self):
        return f"{self.size}"

    def __eq__(self, other):
        return all([
            self.size == other.size,
            self.id == other.id,
        ])


class Sindex(entity.Entity):
    sf: SheetInfo
    position: int
    scroll: int
    size: int
    is_readonly: bool = False
    is_freeze: bool = False
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position})"


class RowSindex(Sindex):
    def __hash__(self):
        return self.id.__hash__()


class ColSindex(Sindex):
    def __hash__(self):
        return self.id.__hash__()


CellValue = Union[int, float, str, bool, None, datetime]
Table = list[list[CellValue]]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(entity.Entity):
    value: CellValue
    row: RowSindex
    col: ColSindex
    sf: SheetInfo
    background: str = 'white'
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"Cell(index=({self.row.position}, {self.col.position}), value={self.value})"

    def __repr__(self):
        return f"Cell(index=({self.row.position}, {self.col.position}), value={self.value})"

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.value == other.value,
            self.row == other.row,
            self.col == other.col,
            self.sf == other.sf,
        ])


class Sheet(BaseModel):
    sf: SheetInfo
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]

    def __init__(self, **data):
        super().__init__(**data)
        assert len(self.rows) == self.sf.size[0]
        assert len(self.cols) == self.sf.size[1]
        assert len(self.cells) == self.sf.size[0] * self.sf.size[1]

    def __eq__(self, other: 'Sheet'):
        if self.sf != other.sf:
            return False
        if len(self.rows) != len(other.rows):
            return False
        for left, right in zip(self.rows, other.rows):
            if left != right:
                return False
        if len(self.cols) != len(other.cols):
            return False
        for left, right in zip(self.cols, other.cols):
            if left != right:
                return False
        if len(self.cells) != len(other.cells):
            return False
        for left, right in zip(self.cells, other.cells):
            if left != right:
                return False
        return True

    def as_table(self) -> list[list[CellValue]]:
        table = []
        for i in range(0, self.sf.size[0]):
            row = []
            for j in range(0, self.sf.size[1]):
                row.append(self.cells[i * self.sf.size[1] + j].value)
            table.append(row)
        return table


class TableInserted(eventbus.Event):
    uuid: UUID = Field(default_factory=uuid4)
    before: tuple[RowSindex, ColSindex]
    table: list[list[CellValue]]
