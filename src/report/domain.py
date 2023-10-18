from typing import Literal, Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.base.entity import Entity

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2', ]
CellValue = Union[int, float, str, bool, None, datetime, ]
CellDtype = Literal["int", "float", "string", "bool", "datetime", ]


class SourceInfo(BaseModel):
    title: str
    id: UUID = Field(default_factory=uuid4)


class Wire(Entity):
    date: datetime
    sender: float
    receiver: float
    amount: float
    sub1: str = ""
    sub2: str = ""
    source_info: SourceInfo
    id: UUID = Field(default_factory=uuid4)


class Source(BaseModel):
    source_info: SourceInfo
    wires: list[Wire] = Field(default_factory=list)


class PlanItems(BaseModel):
    ccols: list[Ccol]
    table: list[list[CellValue]] = Field(default_factory=list)
    uniques: dict[str, int] = Field(default_factory=dict)


class Group(Entity):
    title: str
    plan_items: PlanItems
    source_info: SourceInfo
    id: UUID = Field(default_factory=uuid4)
