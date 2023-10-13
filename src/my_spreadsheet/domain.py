from typing import Union, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: UUID

    def __hash__(self):
        return self.id.__hash__()


class SheetInfo(Entity):
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


class Sindex(Entity):
    sf: SheetInfo
    position: int
    id: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __eq__(self, other: 'Sindex'):
        return all([
            self.sf == other.sf,
            self.position == other.position,
            self.id == other.id,
        ])


class RowSindex(Sindex):
    def __hash__(self):
        return self.id.__hash__()


class ColSindex(Sindex):
    def __hash__(self):
        return self.id.__hash__()


CellValue = Union[int, float, str, bool, None, datetime]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(Entity):
    value: CellValue
    row: RowSindex
    col: ColSindex
    sf: SheetInfo
    id: UUID = Field(default_factory=uuid4)

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


class Sheet(Entity):
    sf: SheetInfo
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]
    id: UUID = Field(default_factory=uuid4)

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
