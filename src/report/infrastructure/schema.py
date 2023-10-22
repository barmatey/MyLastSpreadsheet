import typing
from datetime import datetime
from uuid import UUID

import pandas as pd
from pydantic import BaseModel

from .. import domain


class IntervalCreateSchema(BaseModel):
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


class ReportCreateSchema(BaseModel):
    title: str
    ccols: list[domain.Ccol]
    source_id: UUID
    interval: IntervalCreateSchema
