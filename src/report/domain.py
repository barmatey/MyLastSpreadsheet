from typing import Literal, Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sortedcontainers import SortedList

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2', ]
CellValue = Union[int, float, str, bool, None, datetime, ]
Table = list[list[CellValue]]
CellDtype = Literal["int", "float", "string", "bool", "datetime", ]


class SourceInfo(BaseModel):
    title: str
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        return self.id.__hash__()


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
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Group(BaseModel):
    title: str
    plan_items: PlanItems
    source_info: SourceInfo
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        return self.id.__hash__()


class Period(BaseModel):
    from_date: datetime
    to_date: datetime


class Report(BaseModel):
    periods: list[Period]
    plan_items: PlanItems
    sheet_id: UUID
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        return self.id.__hash__()
