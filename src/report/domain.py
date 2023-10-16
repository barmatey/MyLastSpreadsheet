from typing import Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.base.entity import Entity

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2', ]


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


class PlanItems(Entity):
    ccols: list[Ccol]
    uniques: dict[str, int] = Field(default_factory=dict)
    id: UUID = Field(default_factory=uuid4)


class SheetInfo(Entity):
    pass


class Group(Entity):
    title: str
    plan_items: PlanItems
    source_info: SourceInfo
    sheet_info: SheetInfo
    id: UUID = Field(default_factory=uuid4)
