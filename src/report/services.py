from abc import ABC, abstractmethod
from uuid import UUID
import bisect

import pandas as pd
from sortedcontainers import SortedList

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


class GroupPublisher(subscriber.SourceSubscriber):
    def __init__(self, entity: domain.Group, broker: BrokerService, queue: eventbus.Queue,
                 repo: repository.Repository[domain.Group]):
        self._queue = queue
        self._broker = broker
        self._entity = entity
        self._repo = repo
        self.__appended_rows: list[tuple[int, list[domain.CellValue]]] = []

    def __append_wire(self, wire: domain.Wire):
        cells = [wire.__getattribute__(ccol) for ccol in self._entity.plan_items.ccols]
        key = str(cells)
        if self._entity.plan_items.uniques.get(key) is None:
            self._entity.plan_items.uniques[key] = 0
            bisect.insort(self._entity.plan_items.table, cells, key=lambda x: str(x))
            # todo I need to use binary search here
            for i, item in enumerate(self._entity.plan_items.table):
                if str(item) == str(cells):
                    self.__appended_rows.append((i + 1, cells))
                    break
        self._entity.plan_items.uniques[key] += 1

    async def follow_source(self, source: domain.Source):
        self._entity.plan_items.uniques = {}
        self._entity.plan_items.table = []
        await self.on_wires_appended(source.wires)
        await self._broker.subscribe([source.source_info], self._entity)

    async def on_wires_appended(self, wires: list[domain.Wire]):
        for wire in wires:
            self.__append_wire(wire)
        await self._repo.update_one(self._entity)
        self._queue.append(
            events.GroupRowsInserted(key='GroupRowsInserted', rows=self.__appended_rows, group_info=self._entity))


class GroupService:
    def __init__(self, repo: repository.Repository[domain.Group], subfac: subscriber.SubscriberFactory):
        self._repo = repo
        self._subfac = subfac

    async def create(self, title: str, source: domain.Source, ccols: list[domain.Ccol]) -> domain.Group:
        plan_items = domain.PlanItems(ccols=ccols)
        group = domain.Group(title=title, plan_items=plan_items, source_info=source.source_info)
        await self._repo.add_many([group])
        await self._subfac.create_source_subscriber(group).follow_source(source)
        return group

    async def get_by_id(self, uuid: UUID) -> domain.Group:
        return await self._repo.get_one_by_id(uuid)


class GroupHandler:
    def __init__(self, subfac: subscriber.SubscriberFactory, broker: BrokerService):
        self._subfac = subfac
        self._broker = broker

    async def handle_group_rows_inserted(self, event: events.GroupRowsInserted):
        subs = await self._broker.get_subs(event.group_info)
        for sub in subs:
            await self._subfac.create_group_subscriber(sub).on_group_rows_inserted(event.rows)


class SheetGateway(ABC):
    @abstractmethod
    async def create_sheet(self, table: domain.Table = None) -> UUID:
        raise NotImplemented

    @abstractmethod
    async def get_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.CellValue:
        raise NotImplemented

    @abstractmethod
    async def update_cell_value(self, sheet_id: UUID, row_pos: int, col_pos: int, value: domain.CellValue):
        raise NotImplemented

    @abstractmethod
    async def insert_row_from_position(self, sheet_id: UUID, from_pos: int, row: list[domain.CellValue]):
        raise NotImplemented


async def calculate_profit_cell(wires: pd.DataFrame, ccols: list[domain.Ccol], mappers: list[domain.CellValue],
                                period: domain.Period) -> float:
    conditions = (wires['date'] >= period.from_date) & (wires['date'] <= period.to_date)
    for ccol, x in zip(ccols, mappers):
        conditions = conditions & (wires[ccol] == x)

    amount = wires.loc[conditions]['amount'].sum()
    return amount


class ReportPublisher(subscriber.SourceSubscriber):
    def __init__(self, entity: domain.Report, sheet_gw: SheetGateway, broker: BrokerService):
        self._entity = entity
        self._broker = broker
        self._sheet_gw = sheet_gw

    async def follow_source(self, source: domain.Source):
        await self._broker.subscribe([source.source_info], self._entity)

    async def on_wires_appended(self, wires: list[domain.Wire]):
        for wire in wires:
            await self.__append_wire(wire)

    async def __append_wire(self, wire: domain.Wire):
        cells = [wire.__getattribute__(ccol) for ccol in self._entity.plan_items.ccols]
        key = str(cells)
        if self._entity.plan_items.uniques.get(key) is None:
            self._entity.plan_items.uniques[key] = 0

            row: list[domain.CellValue] = [wire.__getattribute__(c)
                                           for c in self._entity.plan_items.ccols] + [0] * len(self._entity.periods)
            for j, period in enumerate(self._entity.periods, start=len(self._entity.plan_items.ccols)):
                if period.from_date <= wire.date <= period.to_date:
                    row[j] = wire.amount
                    break
            await self._sheet_gw.insert_row_from_position(
                sheet_id=self._entity.sheet_id,
                from_pos=len(self._entity.plan_items.uniques),
                row=row,
            )
        else:
            print('\n', self._entity.plan_items.uniques)
            raise Exception
        self._entity.plan_items.uniques[key] += 1


class ReportService:
    def __init__(self, repo: repository.Repository[domain.Report], sheet_gateway: SheetGateway,
                 subfac: subscriber.SubscriberFactory):
        self._subfac = subfac
        self._gateway = sheet_gateway
        self._repo = repo

    async def create(self, source: domain.Source, plan_items: domain.PlanItems,
                     periods: list[domain.Period]) -> domain.Report:
        wires = pd.DataFrame.from_records([x.model_dump(exclude={'source_info'}) for x in source.wires])
        table = [[None] * len(plan_items.ccols) + [x.to_date for x in periods]]
        for i, row in enumerate(plan_items.table):
            row = row + [await calculate_profit_cell(wires, plan_items.ccols, plan_items.table[i], x) for x in periods]
            table.append(row)

        sheet_id = await self._gateway.create_sheet(table)
        report = domain.Report(sheet_id=sheet_id, periods=periods, plan_items=plan_items)
        await self._subfac.create_source_subscriber(report).follow_source(source)
        await self._repo.add_many([report])
        return report

    async def get_by_id(self, uuid: UUID) -> domain.Report:
        return await self._repo.get_one_by_id(uuid)
