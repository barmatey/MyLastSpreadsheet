from typing import Literal, Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sortedcontainers import SortedList

Ccol = Literal['currency', 'sender', 'receiver', 'sub1', 'sub2']
CellValue = Union[int, float, str, bool, None, datetime]
Table = list[list[CellValue]]
CellDtype = Literal["int", "float", "string", "bool", "datetime"]


class Cell(BaseModel):
    id: UUID
    value: CellValue


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
    order: SortedList[str] = Field(default_factory=SortedList)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_json(self):
        return {
            "ccols": self.ccols,
            "uniques": self.uniques,
            "order": list(self.order),
        }


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

    def find_col_pos(self, date: datetime) -> int:
        for j, period in enumerate(self.periods, start=len(self.plan_items.ccols)):
            if period.from_date <= date <= period.to_date:
                return j
        raise LookupError

    def find_row_pos(self, key: str):
        return self.plan_items.order.bisect_left(key)
