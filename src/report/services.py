from abc import ABC, abstractmethod
from typing import Self
from uuid import UUID

import numpy as np
import pandas as pd
from sortedcontainers import SortedList

from src.base import eventbus
from src.base.broker import Broker
from src.base.repo.repository import Repository
from src.core import OrderBy, Table

from src.sheet import domain as sheet_domain
from . import domain, subscriber, events


class SourceRepo(ABC):
    @property
    def source_info_repo(self) -> Repository[domain.SourceInfo]:
        raise NotImplemented

    @property
    def wire_repo(self) -> Repository[domain.Wire]:
        raise NotImplemented

    @abstractmethod
    async def add_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        raise NotImplemented


class SourceService:
    def __init__(self, repo: SourceRepo, queue: eventbus.Queue):
        self._queue = queue
        self._repo = repo

    async def create_source(self, source: domain.Source):
        await self._repo.add_source(source)

    async def delete_source_by_id(self, uuid: UUID):
        await self._repo.wire_repo.remove_many(filter_by={"source_id": uuid})
        await self._repo.source_info_repo.remove_many(filter_by={"id": uuid})

    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        return await self._repo.get_source_by_id(uuid)

    async def get_source_info_by_id(self, uuid: UUID) -> domain.SourceInfo:
        return await self._repo.source_info_repo.get_one_by_id(uuid)

    async def get_source_info_list(self) -> list[domain.SourceInfo]:
        return await self._repo.source_info_repo.get_many()

    async def get_wires(self, filter_by: dict, order_by: OrderBy = None,
                        slice_from: int = None, slice_to: int = None) -> list[domain.Wire]:
        return await self._repo.wire_repo.get_many(filter_by, order_by, slice_from, slice_to)

    async def get_uniques(self, by_fields: list[str], filter_by: dict, order_by: OrderBy = None) -> list[domain.Wire]:
        return await self._repo.wire_repo.get_uniques(by_fields, filter_by, order_by)

    async def update_wires(self, source_info: domain.SourceInfo, wires: list[domain.Wire]):
        old_wires = await self._repo.wire_repo.get_many_by_id([x.id for x in wires])
        await self.delete_wires(source_info, old_wires)
        await self.append_wires(source_info, wires)

    async def append_wires(self, source_info: domain.SourceInfo, wires: list[domain.Wire]):
        await self._repo.wire_repo.add_many(wires)
        self._queue.append(events.WiresAppended(key='WiresAppended', wires=wires, source_info=source_info))

    async def delete_wires(self, source_info: domain.SourceInfo, wires: list[domain.Wire]):
        await self._repo.wire_repo.remove_many(filter_by={"id.__in": [x.id for x in wires]})
        self._queue.append(events.WiresDeleted(key="WiresDeleted", wires=wires, source_info=source_info))


class SourceHandler:
    def __init__(self, subfac: subscriber.SubscriberFactory, broker: Broker):
        self._subfac = subfac
        self._broker = broker

    async def handle_wires_appended(self, event: events.WiresAppended):
        subs = await self._broker.get_subs(event.source_info)
        for sub in subs:
            await self._subfac.create_source_subscriber(sub).on_wires_appended(event.wires)

    async def handle_wires_deleted(self, event: events.WiresDeleted):
        subs = await self._broker.get_subs(event.source_info)
        for sub in subs:
            await self._subfac.create_source_subscriber(sub).on_wires_deleted(event.wires)


class SheetGateway(ABC):
    @abstractmethod
    async def get_sheet_by_id(self, sheet_id: UUID) -> sheet_domain.Sheet:
        raise NotImplemented

    @abstractmethod
    async def create_sheet(self, table: Table[domain.CellValue] = None) -> UUID:
        raise NotImplemented

    @abstractmethod
    async def update_sheet(self, data: sheet_domain.Sheet):
        raise NotImplemented

    @abstractmethod
    async def merge_sheets(self, target_sheet_id: UUID, data: sheet_domain.Sheet, merge_on: list[int]):
        raise NotImplemented


class Finrep:
    def __init__(self, wire_df: pd.DataFrame, ccols: list[domain.Ccol], interval: domain.Interval):
        self._wire_df = wire_df.copy()
        self._ccols = ccols
        self._interval = interval

        self._report_df = None

    def validate(self) -> Self:
        if self._wire_df.isna().sum().sum() != 0:
            raise ValueError(f"wire_df contains {self._wire_df.isna().sum().sum()} NaNs")
        return self

    def create_report_df(self) -> Self:
        wires: pd.DataFrame = self._wire_df.copy()
        wires['interval'] = pd.cut(wires['date'], self._interval.to_date_range(), right=True)

        needed_cols = ['interval'] + self._ccols + ['amount']
        wires = (
            wires[needed_cols]
            .groupby(needed_cols[:-1], observed=False)
            .sum()
            .reset_index()
            .set_index(self._ccols)
        )

        self._report_df = self._split_df_by_intervals(wires)
        return self

    def drop_zero_rows(self) -> Self:
        self._report_df = self._report_df.replace(0, np.nan)
        self._report_df = self._report_df.dropna(axis=0, how='all')
        self._report_df = self._report_df.replace(np.nan, 0)
        return self

    def drop_zero_cols(self) -> Self:
        self._report_df = self._report_df.replace(0, np.nan)
        self._report_df = self._report_df.dropna(axis=1, how='all')
        self._report_df = self._report_df.replace(np.nan, 0)
        return self

    def reset_indexes(self) -> Self:
        df = self._report_df
        self._report_df = df.reset_index().transpose().reset_index().transpose()
        return self

    def round(self, x=2) -> Self:
        self._report_df = self._report_df.round(x)
        return self

    def get_report_df(self) -> pd.DataFrame:
        if self._report_df is None:
            raise Exception('report is None; Did you forgot create_report_df() function?')
        return self._report_df

    def get_as_table(self) -> Table[domain.Cell]:
        raise Exception

    def to_sheet(self, sf: sheet_domain.SheetInfo = None) -> sheet_domain.Sheet:
        if self._report_df is None:
            raise Exception('report is None. Did you forgot create_report_df() function?')
        if sf is None:
            sf = sheet_domain.SheetInfo(title="Report")

        size = (len(self._report_df.index), len(self._report_df.columns))

        rows = [sheet_domain.RowSindex(sheet_id=sf.id, position=i) for i in range(0, size[0])]
        rows[0].is_freeze = True

        cols = [sheet_domain.ColSindex(sheet_id=sf.id, position=j) for j in range(0, size[1])]
        for j in range(0, len(self._ccols)):
            cols[j].is_freeze = True

        table = []
        for i in range(0, size[0]):
            cells = []
            for j in range(0, size[1]):
                cells.append(sheet_domain.Cell(
                    row_id=rows[i].id,
                    col_id=cols[j].id,
                    sheet_id=sf.id,
                    value=self._report_df.iloc[i, j],
                    background="#F8FAFDFF" if i == 0 or j < len(self._ccols) else "white"
                ))
            table.append(cells)
        return sheet_domain.Sheet(rows=rows, cols=cols, table=table, sf=sf)

    @staticmethod
    def _split_df_by_intervals(df: pd.DataFrame) -> pd.DataFrame:
        if 'interval' not in df.columns:
            raise ValueError('"interval" not in df.columns')
        if len(df.columns) > 2:
            raise ValueError(f'function expected df with to columns only (and the first column must be "interval")'
                             f'real columns are: {df.columns}')

        splited = []
        columns = []

        for interval in df['interval'].unique():
            series = df.loc[df['interval'] == interval].drop('interval', axis=1)
            splited.append(series)
            columns.append(interval.right)
        splited = pd.concat(splited, axis=1).fillna(0)
        splited.columns = columns
        return splited


class ReportPublisher(subscriber.SourceSubscriber):
    def __init__(self, entity: domain.Report, repo: Repository[domain.Report],
                 sheet_gw: SheetGateway, broker: Broker):
        self._entity = entity
        self._broker = broker
        self._sheet_gw = sheet_gw
        self._repo = repo

    async def follow_source(self, source: domain.Source):
        self._entity.plan_items = domain.PlanItems(ccols=self._entity.plan_items.ccols)
        wires = [x.model_dump(exclude={'source_info'}) for x in source.wires]
        wires = pd.DataFrame.from_records(wires)
        wires = wires.loc[
            (wires['date'] >= self._entity.interval.start_date)
            & (wires['date'] <= self._entity.interval.end_date)
            ]
        wires['key'] = ''
        for ccol in self._entity.plan_items.ccols:
            wires['key'] += wires[ccol].astype(str)
        pl = wires.groupby('key')['id'].count().to_dict()
        self._entity.plan_items.uniques = pl
        self._entity.plan_items.order = SortedList(pl.keys())

        sheet = (
            Finrep(wires, self._entity.plan_items.ccols, self._entity.interval)
            .validate()
            .create_report_df()
            .drop_zero_rows()
            .drop_zero_cols()
            .round()
            .reset_indexes()
            .to_sheet(sf=sheet_domain.SheetInfo(id=self._entity.sheet_info.id, title="Report"))
        )
        await self._sheet_gw.update_sheet(data=sheet)
        await self._broker.subscribe([source.source_info], self._entity)

    async def on_wires_appended(self, wires: list[domain.Wire]):
        wires = pd.DataFrame([x.model_dump(exclude={'source_info'}) for x in wires])
        sheet = (
            Finrep(wires, self._entity.plan_items.ccols, self._entity.interval)
            .validate()
            .create_report_df()
            .drop_zero_rows()
            .drop_zero_cols()
            .round()
            .reset_indexes()
            .to_sheet()
        )
        merge_on = list(range(0, len(self._entity.plan_items.ccols)))
        await self._sheet_gw.merge_sheets(self._entity.sheet_info.id, sheet, merge_on)

    async def on_wires_deleted(self, wires: list[domain.Wire]):
        wires = pd.DataFrame([x.model_dump(exclude={'source_info'}) for x in wires])
        wires["amount"] = -wires["amount"]
        sheet = (
            Finrep(wires, self._entity.plan_items.ccols, self._entity.interval)
            .validate()
            .create_report_df()
            .drop_zero_cols()
            .drop_zero_rows()
            .round()
            .reset_indexes()
            .to_sheet()
        )
        merge_on = list(range(0, len(self._entity.plan_items.ccols)))
        await self._sheet_gw.merge_sheets(self._entity.sheet_info.id, sheet, merge_on)


class ReportService:
    def __init__(self, repo: Repository[domain.Report], sheet_gateway: SheetGateway,
                 subfac: subscriber.SubscriberFactory):
        self._subfac = subfac
        self._gateway = sheet_gateway
        self._repo = repo

    async def create(self,
                     title: str,
                     source: domain.Source,
                     plan_items: domain.PlanItems,
                     interval: domain.Interval) -> domain.Report:
        sheet_id = await self._gateway.create_sheet()
        report = domain.Report(
            title=title,
            source_info=source.source_info,
            sheet_info=domain.SheetInfo(id=sheet_id),
            interval=interval,
            plan_items=plan_items,
            category="PROFIT",
        )
        await self._subfac.create_source_subscriber(report).follow_source(source)
        await self._repo.add_many([report])
        return report

    async def get_by_id(self, uuid: UUID) -> domain.Report:
        return await self._repo.get_one_by_id(uuid)

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None) -> list[domain.Report]:
        return await self._repo.get_many(filter_by, order_by)

    async def delete_many(self, filter_by: dict) -> None:
        await self._repo.remove_many(filter_by)
