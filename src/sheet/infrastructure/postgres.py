from datetime import datetime
from typing import Type
from uuid import UUID

import pandas as pd
from sqlalchemy import select, Integer, ForeignKey, String, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import count

from src.core import OrderBy
from src.base.repo.repository import Repository
from src.base.repo.postgres import Base, PostgresRepo

from ..domain import SheetInfo, RowSindex, ColSindex, Cell, CellValue, CellDtype, Sheet
from ..services import SheetRepository, CellRepository, Slice
from ...helpers.arrays import flatten


class SheetInfoModel(Base):
    __tablename__ = "sheet"
    title: Mapped[str] = mapped_column(String(64))
    row_sindexes = relationship('RowSindexModel')
    col_sindexes = relationship('ColSindexModel')
    cells = relationship('CellModel')

    def to_entity(self) -> SheetInfo:
        return SheetInfo(id=self.id, title=self.title)

    @classmethod
    def from_entity(cls, entity: SheetInfo):
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

    def to_entity(self) -> RowSindex:
        return RowSindex(id=self.id, sheet_id=self.sheet_id, position=self.position,
                         is_readonly=self.is_readonly, is_freeze=self.is_freeze, size=self.size)

    @classmethod
    def from_entity(cls, entity: RowSindex):
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

    def to_entity(self) -> ColSindex:
        return ColSindex(id=self.id, sheet_id=self.sheet_id, position=self.position,
                         is_readonly=self.is_readonly, is_freeze=self.is_freeze, size=self.size)

    @classmethod
    def from_entity(cls, entity: ColSindex):
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

    @staticmethod
    def __get_value(value: str, dtype: CellDtype) -> CellValue:
        if dtype == "string":
            return value
        if dtype == "int":
            return int(value)
        if dtype == "float":
            return float(value)
        if dtype == "bool" and value == "True":
            return True
        if dtype == "bool" and value == "False":
            return False
        if dtype == "datetime":
            return datetime.fromisoformat(value)
        raise TypeError(f"{value}, {dtype}")

    @staticmethod
    def __get_dtype(value: CellValue) -> CellDtype:
        if value is None:
            return "string"
        if isinstance(value, int):
            return "int"
        if isinstance(value, str):
            return "string"
        if isinstance(value, float):
            return "float"
        if isinstance(value, datetime):
            return "datetime"
        if isinstance(value, bool):
            return "bool"
        raise TypeError

    def to_entity(self, row, col):
        return Cell(
            id=self.id,
            sheet_id=self.sheet_id,
            row=row,
            col=col,
            value=self.__get_value(self.value, self.dtype),
            background=self.background,
        )

    @classmethod
    def from_entity(cls, entity: Cell):
        return cls(
            id=entity.id,
            value=str(entity.value),
            dtype=cls.__get_dtype(entity.value),
            background=entity.background,
            sheet_id=entity.sheet_id,
            row_sindex_id=entity.row.id,
            col_sindex_id=entity.col.id,
        )


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


class CellPostgresRepo(PostgresRepo, CellRepository):
    def __init__(self, session: AsyncSession, model: Type[Base] = CellModel):
        super().__init__(session, model)

    async def get_sliced_cells(self, sheet_id: UUID, slice_rows: Slice = None,
                               slice_cols: Slice = None) -> list[Cell]:
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
        entities: list[Cell] = [x.to_entity() for x in data]
        return entities

    async def update_cell_by_position(self, sheet_id: UUID, row_pos: int, col_pos: int, data: dict):
        raise NotImplemented

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list[Cell]:
        stmt = (
            select(CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
        )
        stmt = self._expand_statement(stmt, filter_by, order_by, slice_from, slice_to)
        data = await self._session.scalars(stmt)
        entities: list[Cell] = [x.to_entity() for x in data]
        return entities

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[Cell]:
        stmt = (
            select(CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
            .where(CellModel.id.in_(ids))
        )
        stmt = self._expand_statement(stmt, order_by=order_by)
        data = await self._session.scalars(stmt)
        entities: list[Cell] = [x.to_entity() for x in data]
        return entities


class SheetPostgresRepo(SheetRepository):
    def __init__(self, session: AsyncSession):
        self._sf_repo: Repository[SheetInfo] = SheetInfoPostgresRepo(session)
        self._row_repo: Repository[RowSindex] = RowPostgresRepo(session)
        self._col_repo: Repository[ColSindex] = ColPostgresRepo(session)
        self._cell_repo: CellRepository = CellPostgresRepo(session)
        self._session = session

    @property
    def row_repo(self) -> Repository[RowSindex]:
        return self._row_repo

    @property
    def col_repo(self) -> Repository[ColSindex]:
        return self._col_repo

    @property
    def cell_repo(self) -> CellRepository:
        return self._cell_repo

    @property
    def sheet_info_repo(self) -> Repository[SheetInfo]:
        return self._sf_repo

    async def get_sheet_size(self, sheet_uuid: UUID) -> tuple[int, int]:
        stmt = select(count()).select_from(RowSindexModel).where(RowSindexModel.sheet_id == sheet_uuid)
        row_result = await self._session.scalar(stmt)

        stmt = select(count()).select_from(ColSindexModel).where(ColSindexModel.sheet_id == sheet_uuid)
        col_result = await self._session.scalar(stmt)

        return row_result, col_result

    async def add_sheet(self, sheet: Sheet):
        await self._sf_repo.add_many([sheet.sf])
        if len(sheet.rows) and len(sheet.cols) and len(sheet.table):
            await self._row_repo.add_many(sheet.rows)
            await self._col_repo.add_many(sheet.cols)
            await self._cell_repo.add_many(flatten(sheet.table))

    async def get_sheet_by_id(self, uuid: UUID) -> Sheet:
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
            return Sheet(sf=SheetInfo(id=result[0].id, title=result[0].title))

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

        return Sheet(sf=sf, rows=rows, cols=cols, table=table)
