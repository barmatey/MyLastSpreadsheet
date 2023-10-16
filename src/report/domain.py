from typing import Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from src.spreadsheet import domain as sheet_domain

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2',]


class SourceInfo(BaseModel):
    title: str
    id: UUID = Field(default_factory=uuid4)


class Wire(BaseModel):
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
    uniques: dict[str, int] = Field(default_factory=dict)
    id: UUID = Field(default_factory=uuid4)


class Group(BaseModel):
    plan_items: PlanItems
    sheet_id: UUID
