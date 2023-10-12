from typing import Union, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: UUID


class SheetInfo(Entity):
    id: UUID = Field(default_factory=uuid4)
    size: tuple[int, int]


class Sindex(Entity):
    sheet_info: SheetInfo
    position: int
    id: UUID = Field(default_factory=uuid4)


class RowSindex(Sindex):
    pass


class ColSindex(Sindex):
    pass


CellValue = Union[int, float, str, bool, None, datetime]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(Entity):
    value: CellValue
    row: RowSindex
    col: ColSindex
    sheet_info: SheetInfo
    id: UUID = Field(default_factory=uuid4)


class Sheet(Entity):
    sf: SheetInfo
    rows: list[RowSindex]
    cols: list[ColSindex]
    cells: list[Cell]
    id: UUID = Field(default_factory=uuid4)
