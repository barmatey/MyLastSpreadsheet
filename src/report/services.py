from abc import ABC, abstractmethod
from uuid import UUID
import pandas as pd

from ..base import eventbus
from ..base.broker import BrokerService
from ..base.repo.repository import Repository

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


class SheetGateway(ABC):
    @abstractmethod
    async def create_sheet(self, table: domain.Table = None) -> UUID:
        raise NotImplemented

    @abstractmethod
    async def get_cell(self, sheet_id: UUID, row_pos: int, col_pos: int) -> domain.Cell:
        raise NotImplemented

    @abstractmethod
    async def update_cell(self, cell: domain.Cell):
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
        await self.on_wires_appended(source.wires)
        await self._broker.subscribe([source.source_info], self._entity)

    async def on_wires_appended(self, wires: list[domain.Wire]):
        for wire in wires:
            await self.__append_wire(wire)

    async def __append_wire(self, wire: domain.Wire):
        cells = [wire.__getattribute__(ccol) for ccol in self._entity.plan_items.ccols]
        key = str(cells)
        if self._entity.plan_items.uniques.get(key) is None:
            self._entity.plan_items.uniques[key] = 0
            self._entity.plan_items.order.add(key)

            row: list[domain.CellValue] = [wire.__getattribute__(c)
                                           for c in self._entity.plan_items.ccols] + [0] * len(self._entity.periods)
            row[self._entity.find_col_pos(wire.date)] = wire.amount
            await self._sheet_gw.insert_row_from_position(
                sheet_id=self._entity.sheet_id,
                from_pos=self._entity.plan_items.order.bisect_left(key) + 1,
                row=row,
            )
        else:
            row_pos = self._entity.plan_items.order.bisect_left(key)
            col_pos = self._entity.find_col_pos(wire.date)
            cell = await self._sheet_gw.get_cell(self._entity.sheet_id, row_pos, col_pos)
            cell.value += wire.amount
            await self._sheet_gw.update_cell(cell)

        self._entity.plan_items.uniques[key] += 1


class ReportService:
    def __init__(self, repo: Repository[domain.Report], sheet_gateway: SheetGateway,
                 subfac: subscriber.SubscriberFactory):
        self._subfac = subfac
        self._gateway = sheet_gateway
        self._repo = repo

    async def create(self, source: domain.Source, plan_items: domain.PlanItems,
                     periods: list[domain.Period]) -> domain.Report:
        first_row = [None] * len(plan_items.ccols) + [x.to_date for x in periods]
        sheet_id = await self._gateway.create_sheet([first_row])
        report = domain.Report(sheet_id=sheet_id, periods=periods, plan_items=plan_items)
        await self._subfac.create_source_subscriber(report).follow_source(source)
        await self._repo.add_many([report])
        return report

    async def get_by_id(self, uuid: UUID) -> domain.Report:
        return await self._repo.get_one_by_id(uuid)
