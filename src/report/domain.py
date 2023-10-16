from typing import Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2',]


class Wire(BaseModel):
    date: datetime
    sender: float
    receiver: float
    amount: float
    sub1: str = ""
    sub2: str = ""
    id: UUID = Field(default_factory=uuid4)


class Source(BaseModel):
    title: str
    wires: list[Wire]
    id: UUID = Field(default_factory=uuid4)


class PlanItems(BaseModel):
    ccols: list[Ccol]
    uniques: dict[str, int] = Field(default_factory=dict)
    id: UUID = Field(default_factory=uuid4)
