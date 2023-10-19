from abc import ABC, abstractmethod
from uuid import UUID

import numpy as np
import pandas as pd
from src.base.repo import repository

from . import domain, subscriber, events
from ..base import eventbus
from ..base.broker import BrokerService


class SourceRepo(ABC):
    @property
    def source_info_repo(self) -> repository.Repository[domain.SourceInfo]:
        raise NotImplemented

    @property
    def wire_repo(self) -> repository.Repository[domain.Wire]:
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

    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        return await self._repo.get_source_by_id(uuid)

    async def append_wires(self, source_info: domain.SourceInfo, wires: list[domain.Wire]):
        await self._repo.wire_repo.add_many(wires)
        self._queue.append(events.WiresAppended(key='WiresAppended', wires=wires, source_info=source_info))


class SourceHandler:
    def __init__(self, subfac: subscriber.SubscriberFactory, broker: BrokerService):
        self._subfac = subfac
        self._broker = broker

    async def handle_wires_appended(self, event: events.WiresAppended):
        subs = await self._broker.get_subs(event.source_info)
        for sub in subs:
            await self._subfac.create_source_subscriber(sub).on_wires_appended(event.wires)


class GroupService:
    def __init__(self, repo: repository.Repository[domain.Group], subfac: subscriber.SubscriberFactory):
        self._repo = repo
        self._subfac = subfac

    async def create(self, title: str, source: domain.Source, ccols: list[domain.Ccol]) -> domain.Group:
        plan_items = domain.PlanItems(ccols=ccols)
        group = domain.Group(title=title, plan_items=plan_items, source_info=source.source_info)
        await self._subfac.create_source_subscriber(group).follow_source(source)
        await self._repo.add_many([group])
        return group

    async def get_by_id(self, uuid: UUID) -> domain.Group:
        return await self._repo.get_one_by_id(uuid)


class SheetGateway(ABC):
    @abstractmethod
    async def create_sheet(self, table: list[list[domain.CellValue]]) -> UUID:
        raise NotImplemented

    @abstractmethod
    async def get_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.CellValue:
        raise NotImplemented

    @abstractmethod
    async def update_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int, value: domain.CellValue):
        raise NotImplemented


async def calculate_profit_cell(wires: pd.DataFrame, ccols: list[domain.Ccol], mappers: list[domain.CellValue],
                                period: domain.Period) -> float:
    conditions = (wires['date'] >= period.from_date) & (wires['date'] <= period.to_date)
    for ccol, x in zip(ccols, mappers):
        conditions = conditions & (wires[ccol] == x)

    amount = wires.loc[conditions]['amount'].sum()
    return amount


class ReportService:
    def __init__(self, repo: repository.Repository[domain.Report], sheet_gateway: SheetGateway):
        self._gateway = sheet_gateway
        self._repo = repo

    async def create(self, source: domain.Source, group: domain.Group, periods: list[domain.Period]) -> domain.Report:
        wires = pd.DataFrame.from_records([x.model_dump(exclude={'source_info'}) for x in source.wires])
        table = [[None] * len(group.plan_items.ccols) + [x.to_date for x in periods]]
        for i, row in enumerate(group.plan_items.table):
            row = row + [await calculate_profit_cell(wires, group.plan_items.ccols, group.plan_items.table[i], period)
                         for period in periods]
            table.append(row)

        sheet_id = await self._gateway.create_sheet(table)
        report = domain.Report(periods=periods, sheet_id=sheet_id)
        await self._repo.add_many([report])
        return report

    async def get_by_id(self, uuid: UUID) -> domain.Report:
        return await self._repo.get_one_by_id(uuid)
