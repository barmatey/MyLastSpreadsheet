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

    def to_interval(self) -> domain.Interval:
        if self.period_day:
            freq = f"{self.period_day}D"
        elif self.period_month:
            freq = f"{self.period_month}M"
        else:
            freq = f"{self.period_year}"
        return domain.Interval(
            start_date=self.start_date,
            end_date=self.end_date,
            freq=freq,
        )

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
    def from_interval(cls, entity: domain.Interval) -> 'IntervalSchema':
        return cls(
            period_day=777,
            period_month=777,
            period_year=777,
            start_date=entity.start_date,
            end_date=entity.end_date,
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
    sheet_info: domain.SheetInfo

    @classmethod
    def from_entity(cls, entity: domain.Report):
        return cls(
            id=entity.id,
            title=entity.title,
            interval=IntervalSchema.from_interval(entity.interval),
            updated_at=entity.updated_at,
            category="TEST_CATEGORY",
            source_info=entity.source_info,
            sheet_info=entity.sheet_info
        )
