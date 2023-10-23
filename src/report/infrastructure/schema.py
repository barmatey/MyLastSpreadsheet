import typing
from datetime import datetime
from uuid import UUID

import pandas as pd
from pydantic import BaseModel

from .. import domain


class IntervalSchema(BaseModel):
    period_year: int
    period_month: int
    period_day: int
    start_date: datetime
    end_date: datetime
    total_start_date: typing.Optional[datetime] = None
    total_end_date: typing.Optional[datetime] = None

    def to_periods(self) -> list[domain.Period]:
        if self.period_day:
            freq = f"{self.period_day}D"
        elif self.period_month:
            freq = f"{self.period_month}M"
        else:
            freq = f"{self.period_year}"
        periods = pd.date_range(start=self.start_date, end=self.end_date, freq=freq)
        result = [domain.Period(from_date=start, to_date=end) for start, end in zip(periods[0:-1], periods[1:])]
        return result

    @classmethod
    def from_periods(cls, data: list[domain.Period]):
        return cls(
            start_date=data[0].from_date,
            end_date=data[-1].to_date,
            period_day=777,
            period_month=777,
            period_year=777,
        )


class ReportCreateSchema(BaseModel):
    title: str
    ccols: list[domain.Ccol]
    source_id: UUID
    interval: IntervalSchema


class SheetSchema(BaseModel):
    id: UUID


class ReportRetrieveSchema(BaseModel):
    id: UUID
    title: str
    interval: IntervalSchema
    updated_at: datetime
    category: str
    source_info: domain.SourceInfo
    sheet_info: SheetSchema

    @classmethod
    def from_entity(cls, entity: domain.Report):
        return cls(
            id=entity.id,
            title=entity.title,
            interval=IntervalSchema.from_periods(entity.periods),
            updated_at=entity.updated_at,
            category="TEST_CATEGORY",
            source_info=entity.source_info,
            sheet_info=SheetSchema(id=entity.sheet_id)
        )
