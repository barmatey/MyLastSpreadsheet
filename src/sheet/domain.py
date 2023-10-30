from datetime import datetime
from typing import Literal, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


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
