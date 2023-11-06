from abc import ABC, abstractmethod
from typing import Iterable
from uuid import UUID, uuid4

from src.base.repo.repository import Repository
from . import domain
from .. import helpers
from ..base.broker import Broker
from ..base.eventbus import Queue, Updated

Slice = tuple[int, int] | int


class CellRepository(Repository, ABC):
    @abstractmethod
    async def get_sliced_cells(self, sheet_id: UUID, slice_rows: Slice = None,
                               slice_cols: Slice = None) -> list[domain.Cell]:
        raise NotImplemented

    @abstractmethod
    async def update_cell_by_position(self, sheet_id: UUID, row_pos: int, col_pos: int, data: dict):
        raise NotImplemented


class SheetRepository(ABC):
    @property
    def sheet_info_repo(self) -> Repository[domain.SheetInfo]:
        raise NotImplemented

    @property
    def row_repo(self) -> Repository[domain.RowSindex]:
        raise NotImplemented

    @property
    def col_repo(self) -> Repository[domain.ColSindex]:
        raise NotImplemented

    @property
    def cell_repo(self) -> CellRepository:
        raise NotImplemented

    @property
    def formula_repo(self) -> Repository[domain.Formula]:
        raise NotImplemented

    @abstractmethod
    async def add_sheet(self, sheet: domain.Sheet):
        raise NotImplemented

    @abstractmethod
    async def get_sheet_by_id(self, uuid: UUID) -> domain.Sheet:
        raise NotImplemented

    @abstractmethod
    async def get_sheet_size(self, shet_uuid: UUID) -> tuple[int, int]:
        raise NotImplemented


class UpdateSheetFromDifference:
    def __init__(self, repo: SheetRepository):
        self._repo = repo

    async def update(self, diff: domain.SheetDifference):
        await self._repo.row_repo.add_many(diff.rows_created)
        await self._repo.row_repo.update_many(diff.rows_updated)
        await self._repo.row_repo.remove_many(filter_by={"id.__in": [x.id for x in diff.rows_deleted]})

        await self._repo.col_repo.add_many(diff.cols_created)
        await self._repo.col_repo.update_many(diff.cols_updated)
        await self._repo.col_repo.remove_many(filter_by={"id.__in": [x.id for x in diff.cols_deleted]})

        await self._repo.cell_repo.add_many(diff.cells_created)
        await self._repo.cell_repo.update_many(diff.cells_updated)
        await self._repo.cell_repo.remove_many(filter_by={"id.__in": [x.id for x in diff.cells_deleted]})


class CellService:
    def __init__(self, repo: SheetRepository, queue: Queue):
        self._queue = queue
        self._repo = repo

    async def get_by_id(self, cell_id: UUID) -> domain.Cell:
        return await self._repo.cell_repo.get_one_by_id(cell_id)

    async def update_many(self, data: list[domain.Cell]) -> None:
        cells: dict[UUID, domain.Cell] = {
            x.id: x
            for x in await self._repo.cell_repo.get_many_by_id([x.id for x in data])
        }
        for new_cell in data:
            key = new_cell.id
            cells[key].value = new_cell.value
            self._queue.extend(cells[key].events.parse_events())


class FormulaService:
    def __init__(self, repo: SheetRepository, broker: Broker):
        self._repo = repo
        self._broker = broker

    async def create_one(self, parents: list[domain.Cell], target: domain.Cell, key: str) -> domain.Formula:
        if key == "SUM":
            formula = domain.Sum(cell_id=target.id, value=0)
        else:
            raise ValueError

        await formula.follow_cells(parents)
        await self._repo.formula_repo.add_many([formula])
        await self._broker.subscribe(parents, formula)
        await self._broker.subscribe([formula], target)
        return formula

    async def update_many(self, data: list[domain.Formula]) -> None:
        await self._repo.formula_repo.update_many(data)


class SheetService:
    def __init__(self, repo: SheetRepository, cell_service: CellService, formula_service: FormulaService):
        self._repo = repo
        self.cell_service = cell_service
        self.formula_service = formula_service

    async def create_sheet(self, sheet: domain.Sheet = None) -> domain.Sheet:
        if sheet is None:
            sheet = domain.Sheet(sf=domain.SheetInfo(title=""))
        await self._repo.add_sheet(sheet)
        return sheet

    async def get_sheet_by_id(self, sheet_id: UUID) -> domain.Sheet:
        return await self._repo.get_sheet_by_id(sheet_id)

    async def update_sheet(self, sheet: domain.Sheet) -> None:
        old_sheet = await self._repo.get_sheet_by_id(sheet.sf.id)
        diff = domain.SheetDifference.from_sheets(old_sheet, sheet)
        await UpdateSheetFromDifference(repo=self._repo).update(diff)

    async def complex_merge(self, target_id: UUID, data: domain.Sheet, target_on: list[int], data_on: list[int]):
        target = await self._repo.get_sheet_by_id(target_id)
        table = domain.complex_merge(
            lhs=target,
            rhs=data,
            left_on=[target.cols[x].id for x in target_on],
            right_on=[data.cols[x].id for x in data_on],
        )
        merged = target.resize(len(table), len(table[0])).replace_cell_values(table, inplace=True)
        diff = domain.SheetDifference.from_sheets(target, merged)
        await UpdateSheetFromDifference(repo=self._repo).update(diff)


class CreateReportChecker:
    def __init__(self, repo: SheetRepository, broker: Broker):
        self._repo = repo
        self._broker = broker

    async def create(self, base_sheet: domain.Sheet):
        sheet_id = uuid4()
        rows = []
        for parent_row in base_sheet.rows:
            input_row = domain.RowSindex(position=len(rows), size=parent_row.size, sheet_id=sheet_id)
            checker_row = domain.RowSindex(position=len(rows) + 1, size=parent_row.size, sheet_id=sheet_id)
            await self._broker.subscribe([parent_row], input_row)
            if not parent_row.is_freeze:
                await self._broker.subscribe([parent_row], checker_row)
            rows.append(input_row)
            rows.append(checker_row)

        cols = []
        for parent_col in base_sheet.cols:
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
                    parent_cell = base_sheet.table[int(i / 2)][j]
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
                    parent_cell = base_sheet.table[int((i - 1) / 2)][j]
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
                            minuend=(minuend.id, minuend.value),
                            subtrahend=(subtrahend.id, subtrahend.value),
                            cell_id=cell.id,
                        )
                        formulas.append(formula)
                        await self._broker.subscribe([minuend, subtrahend], formula)
                        await self._broker.subscribe([formula], cell)
            table.append(cells)
        sheet = domain.Sheet(sf=domain.SheetInfo(id=sheet_id, title="Checker"),
                             rows=rows, cols=cols, table=table).drop(rows[1].id, axis=0)
        await self._repo.add_sheet(sheet)
        await self._repo.formula_repo.add_many(formulas)

        return sheet


class ReportSheetService:
    def __init__(self, repo: SheetRepository, broker: Broker):
        self._repo = repo
        self._broker = broker

    async def create_checker_sheet(self, base_sheet_id: UUID) -> domain.Sheet:
        base_sheet = await self._repo.get_sheet_by_id(base_sheet_id)
        return await CreateReportChecker(self._repo, self._broker).create(base_sheet)
