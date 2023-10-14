from datetime import datetime
from typing import Type
from uuid import UUID

from sqlalchemy import TIMESTAMP, func, select, update, delete, Integer, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.core import OrderBy
from ..domain import Entity, SheetInfo, RowSindex, ColSindex, Cell, CellValue, CellDtype, Sheet, Sindex
from ..services import Repository, T, SheetRepository
from ... import helpers


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"{self.__class__.__name__}"

    @classmethod
    def from_entity(cls, entity: Entity):
        raise NotImplemented

    def to_entity(self, **kwargs) -> Entity:
        raise NotImplemented


class SheetInfoModel(Base):
    __tablename__ = "sheet"
    row_size: Mapped[int] = mapped_column(Integer, nullable=False)
    col_size: Mapped[int] = mapped_column(Integer, nullable=False)
    row_sindexes = relationship('RowSindexModel')
    col_sindexes = relationship('ColSindexModel')
    cells = relationship('CellModel')

    def to_entity(self) -> SheetInfo:
        return SheetInfo(id=self.id, size=(self.row_size, self.col_size))

    @classmethod
    def from_entity(cls, entity: SheetInfo):
        return cls(
            row_size=entity.size[0],
            col_size=entity.size[1],
            id=entity.id,
        )


class RowSindexModel(Base):
    __tablename__ = "row_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: SheetInfo) -> RowSindex:
        return RowSindex(id=self.id, sf=sheet, position=self.position)

    @classmethod
    def from_entity(cls, entity: RowSindex):
        return cls(
            position=entity.position,
            id=entity.id,
            sheet_id=entity.sf.id,
        )


class ColSindexModel(Base):
    __tablename__ = "col_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("sheet.id"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: SheetInfo) -> ColSindex:
        return ColSindex(id=self.id, sf=sheet, position=self.position)

    @classmethod
    def from_entity(cls, entity: RowSindex):
        return cls(
            position=entity.position,
            id=entity.id,
            sheet_id=entity.sf.id,
        )


class CellModel(Base):
    __tablename__ = "cell"
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    dtype: Mapped[str] = mapped_column(String(8), nullable=False)
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

    def to_entity(self, sheet_info: SheetInfo, row: RowSindex, col: ColSindex):
        return Cell(sf=sheet_info, row=row, col=col, value=self.__get_value(self.value, self.dtype),
                    id=self.id)

    @classmethod
    def from_entity(cls, entity: Cell):
        return cls(
            id=entity.id,
            value=str(entity.value),
            dtype=cls.__get_dtype(entity.value),
            sheet_id=entity.sf.id,
            row_sindex_id=entity.row.id,
            col_sindex_id=entity.col.id,
        )


class PostgresRepo(Repository):

    def __init__(self, model: Type[Base], session: AsyncSession):
        self._model = model
        self._session = session

    async def add_many(self, data: list[T]):
        models = [self._model.from_entity(x) for x in data]
        self._session.add_all(models)

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None) -> list[T]:
        stmt = select(self._model)
        if filter_by is not None:
            stmt = stmt.where(*helpers.postgres.parse_filter_by(self._model, filter_by))
        if order_by is not None:
            stmt = stmt.order_by(*helpers.postgres.parse_order_by(self._model, order_by))
        models = await self._session.execute(stmt)
        entities = [x.to_entity() for x in models]
        return entities

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        stmt = select(self._model).where(self._model.id.in_(ids))
        result = await self._session.execute(stmt)
        entities = [x.to_entity() for x in result]
        return entities

    async def update_one(self, data: T):
        model = self._model.from_entity(data)
        stmt = update(self._model).where(self._model.id == data.id)
        await self._session.execute(stmt, model.__dict__)

    async def update_many(self, data: list[T]):
        stmt = update(self._model)
        data = [self._model.from_entity(x).__dict__ for x in data]
        await self._session.execute(stmt, data)

    async def remove_many(self, data: list[T]):
        ids = [x.id for x in data]
        stmt = delete(self._model).where(self._model.id.in_(ids))
        await self._session.execute(stmt)


class SheetInfoPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SheetInfoModel):
        super().__init__(model, session)


class SindexPostgresRepo(PostgresRepo):
    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None) -> list[T]:
        stmt = (
            select(self._model, SheetInfoModel)
            .join(SheetInfoModel, self._model.sheet_id == SheetInfoModel.id)
        )
        if filter_by is not None:
            stmt = stmt.where(*helpers.postgres.parse_filter_by(self._model, filter_by))
        if order_by is not None:
            stmt = stmt.order_by(*helpers.postgres.parse_order_by(self._model, order_by))

        models = await self._session.execute(stmt)
        sindexes = [x[0].to_entity(x[1].to_entity()) for x in models]
        return sindexes


class RowPostgresRepo(SindexPostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = RowSindexModel):
        super().__init__(model, session)


class ColPostgresRepo(SindexPostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = ColSindexModel):
        super().__init__(model, session)


class CellPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = CellModel):
        super().__init__(model, session)

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None) -> list[T]:
        stmt = (
            select(SheetInfoModel, RowSindexModel, ColSindexModel, CellModel)
            .join(SheetInfoModel, CellModel.sheet_id == SheetInfoModel.id)
            .join(RowSindexModel, CellModel.row_sindex_id == RowSindexModel.id)
            .join(ColSindexModel, CellModel.col_sindex_id == ColSindexModel.id)
        )
        if filter_by is not None:
            stmt = stmt.where(*helpers.postgres.parse_filter_by(self._model, filter_by))
        if order_by is not None:
            stmt = stmt.order_by(*helpers.postgres.parse_order_by(self._model, order_by))
        data = await self._session.execute(stmt)
        entities: list[Cell] = []
        for x in data:
            sheet_info = x[0].to_entity()
            row = x[1].to_entity(sheet=sheet_info)
            col = x[2].to_entity(sheet=sheet_info)
            cell = x[3].to_entity(sheet_info=sheet_info, row=row, col=col)
            entities.append(cell)
        return entities


class SheetPostgresRepo(SheetRepository):
    def __init__(self, session: AsyncSession):
        self._sf_repo: Repository[SheetInfo] = SheetInfoPostgresRepo(session)
        self._row_repo: Repository[RowSindex] = RowPostgresRepo(session)
        self._col_repo: Repository[ColSindex] = ColPostgresRepo(session)
        self._cell_repo: Repository[Cell] = CellPostgresRepo(session)
        self._session = session

    @property
    def row_repo(self) -> Repository[RowSindex]:
        return self._row_repo

    @property
    def col_repo(self) -> Repository[ColSindex]:
        return self._col_repo

    @property
    def cell_repo(self) -> Repository[Cell]:
        return self._cell_repo

    @property
    def sheet_info_repo(self) -> Repository[SheetInfo]:
        return self._sf_repo

    async def add_sheet(self, sheet: Sheet):
        await self._sf_repo.add_many([sheet.sf])
        if len(sheet.rows) and len(sheet.cols) and len(sheet.cells):
            await self._row_repo.add_many(sheet.rows)
            await self._col_repo.add_many(sheet.cols)
            await self._cell_repo.add_many(sheet.cells)

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
            result = list(await self._session.execute(stmt))
            if len(result) != 1:
                raise LookupError
            return Sheet(sf=SheetInfo(size=(0, 0), id=uuid), rows=[], cols=[], cells=[], id=uuid)

        sheet_info: SheetInfo = result[0][0].to_entity()
        rows = [result[x][1].to_entity(sheet_info)
                for x in range(0, sheet_info.size[0] * sheet_info.size[1], sheet_info.size[1])]
        cols = [result[x][2].to_entity(sheet_info) for x in range(0, sheet_info.size[1])]
        cells = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = i * sheet_info.size[1] + j
                cells.append(result[index][3].to_entity(sheet_info, row, col))

        sheet = Sheet(sf=sheet_info, rows=rows, cols=cols, cells=cells, id=sheet_info.id)
        return sheet
