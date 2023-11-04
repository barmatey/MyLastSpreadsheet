from pydantic import BaseModel

from src.base.broker import Broker
from .. import domain, subscriber, services
from ... import helpers


class SumFormula(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Formula, broker: Broker, sheet_service: services.SheetService):
        self._entity = entity
        self._broker = broker
        self._sheet_service = sheet_service

    async def follow_cells(self, pubs: list[domain.Cell]):
        for cell in pubs:
            self._entity.value += cell.value
        await self._sheet_service.formula_service.update_many([self._entity])
        await self._broker.subscribe(pubs, self._entity)

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        raise NotImplemented

    async def on_cell_deleted(self, pub: domain.Cell):
        raise NotImplemented


class ReportCheckerSheet(subscriber.SheetSubscriber):
    def __init__(self, entity: domain.Sheet, broker: Broker, sheet_service: services.SheetService):
        self._entity = entity
        self._broker = broker
        self._sheet_service = sheet_service

    @property
    def entity(self) -> domain.Sheet:
        return self._entity

    @helpers.decorators.async_timeit
    async def follow_sheet(self, pub: domain.Sheet):
        if self._entity.size != (0, 0):
            raise ValueError
        sheet_id = self._entity.sf.id

        rows = []
        for parent_row in pub.rows:
            input_row = domain.RowSindex(position=len(rows), size=parent_row.size, sheet_id=sheet_id)
            checker_row = domain.RowSindex(position=len(rows) + 1, size=parent_row.size, sheet_id=sheet_id)
            await self._broker.subscribe([parent_row], input_row)
            if not parent_row.is_freeze:
                await self._broker.subscribe([parent_row], checker_row)
            rows.append(input_row)
            rows.append(checker_row)

        cols = []
        for parent_col in pub.cols:
            col = domain.ColSindex(position=parent_col.position, size=parent_col.size, sheet_id=sheet_id)
            await self._broker.subscribe([parent_col], col)
            cols.append(col)

        table = []
        formulas = []
        for i, row in enumerate(rows):
            cells = []
            for j, col in enumerate(cols):
                # Input row
                if i % 2 == 0:
                    parent_cell = pub.table[int(i / 2)][j]
                    # Index cell (always equal parent cell)
                    if parent_cell.col.is_freeze or parent_cell.row.is_freeze:
                        value = parent_cell.value
                        bkg = parent_cell.background
                        cell = domain.Cell(row=row, col=col, sheet_id=sheet_id, value=value, background=bkg)
                        cells.append(cell)
                        await self._broker.subscribe([parent_cell], cell)
                    # Input cell
                    else:
                        cells.append(domain.Cell(row=row, col=col, sheet_id=sheet_id, value=0,
                                                 background=parent_cell.background))
                # Checker row
                else:
                    parent_cell = pub.table[int((i - 1) / 2)][j]
                    # Blank cell
                    if parent_cell.col.is_freeze or parent_cell.row.is_freeze:
                        cells.append(domain.Cell(row=row, col=col, sheet_id=sheet_id, value="",
                                                 background=parent_cell.background))
                    # Formula cell
                    else:
                        value = -parent_cell.value
                        bkg = parent_cell.background
                        cell = domain.Cell(row=row, col=col, sheet_id=sheet_id, value=value, background=bkg)
                        cells.append(cell)

                        minuend = table[-1][j]
                        subtrahend = parent_cell
                        formula = domain.Sub(
                            value=minuend.value - subtrahend.value,
                            cell_id=cell.id,
                        )
                        formulas.append(formula)
                        await self._broker.subscribe([minuend, subtrahend], formula)
            table.append(cells)
        self._entity = domain.Sheet(sf=self._entity.sf, rows=rows, cols=cols, table=table).drop(rows[1].id, axis=0)
        await self._sheet_service.update_sheet(self._entity)
        await self._sheet_service.formula_service.create_many(formulas)

    async def unfollow_sheet(self, pub: domain.Sheet):
        pass

    async def on_rows_appended(self, table: list[list[domain.CellValue]]):
        pass

    async def on_sheet_deleted(self):
        pass


class CellSelfSubscriber(subscriber.CellSubscriber):
    def __init__(self, entity: domain.Cell, sheet_service: services.SheetService, broker_service: Broker):
        self._sheet_service = sheet_service
        self._broker_service = broker_service
        self._entity = entity

    async def follow_cells(self, pubs: list[domain.Cell]):
        if len(pubs) != 1:
            raise Exception
        _old = self._entity.model_copy(deep=True)
        self._entity.value = pubs[0].value
        await self._broker_service.subscribe(pubs, self._entity)
        await self._sheet_service.cell_service.update_many([self._entity])

    async def unfollow_cells(self, pubs: list[domain.Cell]):
        raise NotImplemented

    async def on_cell_updated(self, old: domain.Cell, actual: domain.Cell):
        self._entity.value = actual.value
        await self._sheet_service.cell_service.update_many([actual])

    async def on_cell_deleted(self, pub: domain.Cell):
        _old = self._entity.model_copy()
        self._entity.value = "REF_ERROR"
        await self._sheet_service.cell_service.update_many([self._entity])


class SindexSelfSubscriber(subscriber.SindexSubscriber):
    def __init__(self, entity: domain.Sindex, sheet_service: services.SheetService, broker_service: Broker):
        self._entity = entity
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    async def follow_sindexes(self, pubs: list[domain.Sindex]):
        await self._broker_service.subscribe(pubs, self._entity)

    async def unfollow_sindexes(self, pubs: list[domain.Sindex]):
        raise NotImplemented

    async def on_sindex_updated(self, old_value: domain.Sindex, new_value: domain.Sindex):
        pass

    async def on_sindex_deleted(self, pub: domain.Sindex):
        raise NotImplemented


class SubFactory(subscriber.SubscriberFactory):
    def __init__(self, sheet_service: services.SheetService, broker_service: Broker):
        self._sheet_service = sheet_service
        self._broker_service = broker_service

    def create_cell_subscriber(self, entity: BaseModel) -> subscriber.CellSubscriber:
        if isinstance(entity, domain.Cell):
            return CellSelfSubscriber(entity, self._sheet_service, self._broker_service)
        if isinstance(entity, domain.Sum):
            return
        raise TypeError

    def create_sindex_subscriber(self, entity: domain.Sindex) -> subscriber.SindexSubscriber:
        return SindexSelfSubscriber(entity, self._sheet_service, self._broker_service)

    def create_sheet_subscriber(self, entity: BaseModel) -> subscriber.SheetSubscriber:
        if isinstance(entity, domain.Sheet):
            return ReportCheckerSheet(entity, self._broker_service, self._sheet_service)
        raise TypeError
