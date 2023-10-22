from typing import Literal, Union
from typing_extensions import TypedDict
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


class WcolSchema(TypedDict):
    title: str
    label: str
    dtype: Literal["str", "int", "float", "date"]


def wcols_factory():
    return [
        {'title': 'date', 'label': 'Date', 'dtype': 'date', },
        {'title': 'sender', 'label': 'Sender', 'dtype': 'float', },
        {'title': 'receiver', 'label': 'Receiver', 'dtype': 'float', },
        {'title': 'debit', 'label': 'Debit', 'dtype': 'float', },
        {'title': 'credit', 'label': 'Credit', 'dtype': 'float', },
        {'title': 'sub1', 'label': 'First subconto', 'dtype': 'str', },
        {'title': 'sub2', 'label': 'Second subconto', 'dtype': 'str', },
    ]


class SourceInfo(BaseModel):
    title: str
    wcols: list[WcolSchema] = Field(default_factory=wcols_factory)
    id: UUID = Field(default_factory=uuid4)
    total_start_date: datetime = Field(default_factory=datetime.now)
    total_end_date: datetime = Field(default_factory=datetime.now)
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    def to_json(self) -> dict:
        return {
            "periods": [x.model_dump(mode='json') for x in self.periods],
            "plan_items": self.plan_items.to_json(),
            "sheet_id": self.sheet_id,
            "id": self.id,
        }
