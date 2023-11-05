from datetime import datetime
from typing import Type
from uuid import UUID

from sqlalchemy import select, Integer, ForeignKey, String, Boolean, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import count

from src.core import OrderBy
from src.base.repo.repository import Repository
from src.base.repo.postgres import Base, PostgresRepo
from src.helpers.arrays import flatten
from . import helpers

from .. import domain, services


class SheetInfoModel(Base):
    __tablename__ = "sheet"
    title: Mapped[str] = mapped_column(String(64))
    row_sindexes = relationship('RowSindexModel')
    col_sindexes = relationship('ColSindexModel')
    cells = relationship('CellModel')

    def to_entity(self) -> domain.SheetInfo:
        return domain.SheetInfo(id=self.id, title=self.title)

    @classmethod
    def from_entity(cls, entity: domain.SheetInfo):
        return cls(
            id=entity.id,
            title=entity.title,
        )


class RowSindexModel(Base):
    __tablename__ = "row_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_freeze: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cells = relationship('CellModel')

    def to_entity(self) -> domain.RowSindex:
        return domain.RowSindex(id=self.id, sheet_id=self.sheet_id, position=self.position,
                                is_readonly=self.is_readonly, is_freeze=self.is_freeze, size=self.size)

    @classmethod
    def from_entity(cls, entity: domain.RowSindex):
        return cls(
            position=entity.position,
            id=entity.id,
            sheet_id=entity.sheet_id,
            is_readonly=entity.is_readonly,
            is_freeze=entity.is_freeze,
            size=entity.size,
        )


class ColSindexModel(Base):
    __tablename__ = "col_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_freeze: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cells = relationship('CellModel')

    def to_entity(self) -> domain.ColSindex:
        return domain.ColSindex(id=self.id, sheet_id=self.sheet_id, position=self.position,
                                is_readonly=self.is_readonly, is_freeze=self.is_freeze, size=self.size)

    @classmethod
    def from_entity(cls, entity: domain.ColSindex):
        return cls(
            position=entity.position,
            id=entity.id,
            sheet_id=entity.sheet_id,
            is_readonly=entity.is_readonly,
            is_freeze=entity.is_freeze,
            size=entity.size,
        )


class CellModel(Base):
    __tablename__ = "cell"
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    dtype: Mapped[str] = mapped_column(String(8), nullable=False)
    background: Mapped[str] = mapped_column(String(21), default='white')
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    row_sindex_id: Mapped[UUID] = mapped_column(ForeignKey("row_sindex.id"))
    col_sindex_id: Mapped[UUID] = mapped_column(ForeignKey("col_sindex.id"))
    formulas = relationship('FormulaModel')

    def to_entity(self, row, col):
        return domain.Cell(
            id=self.id,
            sheet_id=self.sheet_id,
            row=row,
            col=col,
            value=helpers.get_value(self.value, self.dtype),
            background=self.background,
        )

    @classmethod
    def from_entity(cls, entity: domain.Cell):
        return cls(
            id=entity.id,
            value=str(entity.value),
            dtype=helpers.get_dtype(entity.value),
            background=entity.background,
            sheet_id=entity.sheet_id,
            row_sindex_id=entity.row.id,
            col_sindex_id=entity.col.id,
        )


class FormulaModel(Base):
    __tablename__ = "formula"
    data: Mapped[JSON] = mapped_column(JSON)
    cell_id: Mapped[UUID] = mapped_column(ForeignKey("cell.id"))
    formula_key: Mapped[String] = mapped_column(String(16))

    def to_entity(self, **kwargs) -> domain.Formula:
        if self.formula_key == "SUM":
            return domain.Sum(**self.data, cell_id=self.cell_id)
        if self.formula_key == "SUB":
            return domain.Sub(**self.data, cell_id=self.cell_id)

    @classmethod
    def from_entity(cls, entity: domain.Formula):
        if isinstance(entity, domain.Sum):
            return cls(id=entity.id, data=entity.to_json(), formula_key="SUM", cell_id=entity.cell_id)
        if isinstance(entity, domain.Sub):
            return cls(id=entity.id, data=entity.to_json(), formula_key="SUB", cell_id=entity.cell_id)


class SheetInfoPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SheetInfoModel):
        super().__init__(session, model)


class SindexPostgresRepo(PostgresRepo):
    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list:
        stmt = (
            select(self._model, SheetInfoModel)
            .join(SheetInfoModel, self._model.sheet_id == SheetInfoModel.id)
        )
        stmt = self._expand_statement(stmt, filter_by, order_by, slice_from, slice_to)
        models = await self._session.execute(stmt)
        sindexes = [x[0].to_entity(x[1].to_entity()) for x in models]
        return sindexes


class RowPostgresRepo(SindexPostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = RowSindexModel):
        super().__init__(session, model)


class ColPostgresRepo(SindexPostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = ColSindexModel):
        super().__init__(session, model)


class CellPostgresRepo(PostgresRepo, services.CellRepository):
    def __init__(self, session: AsyncSession, model: Type[Base] = CellModel):
        super().__init__(session, model)

    async def get_sliced_cells(self, sheet_id: UUID, slice_rows: services.Slice = None,
                               slice_cols: services.Slice = None) -> list[domain.Cell]:
        stmt = (
            select(CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
        )

        filters = [SheetInfoModel.id == sheet_id]
        if slice_rows:
            if isinstance(slice_rows, tuple):
                filters.append(RowSindexModel.position >= slice_rows[0])
                filters.append(RowSindexModel.position < slice_rows[1])
            else:
                filters.append(RowSindexModel.position == slice_rows)

        if slice_cols:
            if isinstance(slice_cols, tuple):
                filters.append(ColSindexModel.position >= slice_cols[0])
                filters.append(ColSindexModel.position < slice_cols[1])
            else:
                filters.append(ColSindexModel.position == slice_cols)

        stmt = stmt.where(*filters).order_by(RowSindexModel.position, ColSindexModel.position)
        data = await self._session.scalars(stmt)
        entities: list[domain.Cell] = [x.to_entity() for x in data]
        return entities

    async def update_cell_by_position(self, sheet_id: UUID, row_pos: int, col_pos: int, data: dict):
        raise NotImplemented

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list[domain.Cell]:
        stmt = (
            select(CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
        )
        stmt = self._expand_statement(stmt, filter_by, order_by, slice_from, slice_to)
        data = await self._session.scalars(stmt)
        entities: list[domain.Cell] = [x.to_entity() for x in data]
        return entities

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[domain.Cell]:
        stmt = (
            select(SheetInfoModel, RowSindexModel, ColSindexModel, CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
            .where(CellModel.id.in_(ids))
        )
        stmt = self._expand_statement(stmt, order_by=order_by)
        data = await self._session.execute(stmt)
        entities: list[domain.Cell] = [x[3].to_entity(x[1].to_entity(), x[2].to_entity()) for x in data]
        return entities

    async def get_one_by_id(self, uuid: UUID) -> domain.Cell:
        stmt = (
            select(SheetInfoModel, RowSindexModel, ColSindexModel, CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
            .where(CellModel.id == uuid)
        )
        data = await self._session.execute(stmt)
        entities: list[domain.Cell] = [x[3].to_entity(x[1].to_entity(), x[2].to_entity()) for x in data]
        return entities.pop()


class SheetPostgresRepo(services.SheetRepository):
    def __init__(self, session: AsyncSession):
        self._sf_repo: Repository[domain.SheetInfo] = SheetInfoPostgresRepo(session)
        self._row_repo: Repository[domain.RowSindex] = RowPostgresRepo(session)
        self._col_repo: Repository[domain.ColSindex] = ColPostgresRepo(session)
        self._cell_repo: services.CellRepository = CellPostgresRepo(session)
        self._formula_repo: Repository[domain.Formula] = FormulaPostgresRepo(session)
        self._session = session

    @property
    def row_repo(self) -> Repository[domain.RowSindex]:
        return self._row_repo

    @property
    def col_repo(self) -> Repository[domain.ColSindex]:
        return self._col_repo

    @property
    def cell_repo(self) -> services.CellRepository:
        return self._cell_repo

    @property
    def formula_repo(self) -> Repository[domain.Formula]:
        return self._formula_repo

    @property
    def sheet_info_repo(self) -> Repository[domain.SheetInfo]:
        return self._sf_repo

    async def get_sheet_size(self, sheet_uuid: UUID) -> tuple[int, int]:
        stmt = select(count()).select_from(RowSindexModel).where(RowSindexModel.sheet_id == sheet_uuid)
        row_result = await self._session.scalar(stmt)

        stmt = select(count()).select_from(ColSindexModel).where(ColSindexModel.sheet_id == sheet_uuid)
        col_result = await self._session.scalar(stmt)

        return row_result, col_result

    async def add_sheet(self, sheet: domain.Sheet):
        await self._sf_repo.add_many([sheet.sf])
        if len(sheet.rows) and len(sheet.cols) and len(sheet.table):
            await self._row_repo.add_many(sheet.rows)
            await self._col_repo.add_many(sheet.cols)
            await self._cell_repo.add_many(flatten(sheet.table))

    async def get_sheet_by_id(self, uuid: UUID) -> domain.Sheet:
        stmt = (
            select(SheetInfoModel, RowSindexModel, ColSindexModel, CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
            .order_by(RowSindexModel.position, ColSindexModel.position)
            .where(SheetInfoModel.id == uuid)
        )
        result = list(await self._session.execute(stmt))
        if len(result) == 0:
            stmt = select(SheetInfoModel).where(SheetInfoModel.id == uuid)
            result = list(await self._session.scalars(stmt))
            if len(result) != 1:
                raise LookupError
            return domain.Sheet(sf=domain.SheetInfo(id=result[0].id, title=result[0].title))

        rows = []
        cols = []
        table = []

        sf = result[0][0].to_entity()

        last_row_pos = -1
        for data in result:
            if data[1].position != last_row_pos:
                rows.append(data[1].to_entity())
                table.append([])
                last_row_pos += 1
            if data[1].position == 0:
                cols.append(data[2].to_entity())
            table[-1].append(data[3].to_entity(row=rows[-1], col=cols[len(table[-1])]))

        return domain.Sheet(sf=sf, rows=rows, cols=cols, table=table)


class FormulaPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = FormulaModel):
        super().__init__(session, model)
