from datetime import datetime
from typing import Type
from uuid import UUID

from sqlalchemy import TIMESTAMP, func, insert, select, update, delete, Integer, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.core import OrderBy
from ..domain import Entity, SheetInfo, RowSindex, ColSindex, Cell, CellValue, CellDtype, Sheet
from ..services import Repository, T


class Base(DeclarativeBase):
    uuid: Mapped[UUID] = mapped_column(primary_key=True)
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
        return SheetInfo(id=self.uuid, size=(self.row_size, self.col_size))

    @classmethod
    def from_entity(cls, entity: SheetInfo):
        return cls(
            row_size=entity.size[0],
            col_size=entity.size[1],
            uuid=entity.id,
        )


class RowSindexModel(Base):
    __tablename__ = "row_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: SheetInfo) -> RowSindex:
        return RowSindex(id=self.uuid, sheet_info=sheet, position=self.position)

    @classmethod
    def from_entity(cls, entity: RowSindex):
        return cls(
            position=entity.position,
            uuid=entity.id,
            sheet_uuid=entity.sheet_info.id,
        )


class ColSindexModel(Base):
    __tablename__ = "col_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: SheetInfo) -> ColSindex:
        return ColSindex(id=self.uuid, sheet_info=sheet, position=self.position)

    @classmethod
    def from_entity(cls, entity: RowSindex):
        return cls(
            position=entity.position,
            uuid=entity.id,
            sheet_uuid=entity.sheet_info.id,
        )


class CellModel(Base):
    __tablename__ = "cell"
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    dtype: Mapped[str] = mapped_column(String(8), nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    row_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("row_sindex.uuid"))
    col_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("col_sindex.uuid"))

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
        return Cell(sheet_info=sheet_info, row=row, col=col, value=self.__get_value(self.value, self.dtype),
                    id=self.uuid)

    @classmethod
    def from_entity(cls, entity: Cell):
        return cls(
            uuid=entity.id,
            value=str(entity.value),
            dtype=cls.__get_dtype(entity.value),
            sheet_uuid=entity.sheet_info.id,
            row_sindex_uuid=entity.row.id,
            col_sindex_uuid=entity.col.id,
        )


class PostgresRepo(Repository):

    def __init__(self, model: Type[Base], session: AsyncSession):
        self._model = model
        self._session = session

    async def add_many(self, data: list[T]):
        models = [self._model.from_entity(x) for x in data]
        stmt = insert(self._model)
        await self._session.execute(stmt, models)

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        stmt = select(self._model).where(self._model.uuid.in_(ids))
        result = await self._session.execute(stmt)
        entities = [x.to_entity() for x in result]
        return entities

    async def update_one(self, data: T):
        model = self._model.from_entity(data)
        stmt = update(self._model).where(self._model.uuid == data.id).values(model)
        await self._session.execute(stmt)

    async def remove_many(self, data: list[T]):
        ids = [x.id for x in data]
        stmt = delete(self._model).where(self._model.uuid.in_(ids))
        await self._session.execute(stmt)


class SheetInfoPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = SheetInfoModel):
        super().__init__(model, session)


class RowPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = RowSindexModel):
        super().__init__(model, session)


class ColPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = ColSindexModel):
        super().__init__(model, session)


class CellPostgresRepo(PostgresRepo):
    def __init__(self, session: AsyncSession, model: Type[Base] = CellModel):
        super().__init__(model, session)


class SheetPostgresRepo(Repository):
    def __init__(self, session: AsyncSession):
        self._sf_repo = SheetInfoPostgresRepo(session)
        self._row_repo = RowPostgresRepo(session)
        self._col_repo = ColPostgresRepo(session)
        self._cell_repo = CellPostgresRepo(session)

    async def add_many(self, data: list[Sheet]):
        pass

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[Sheet]:
        pass

    async def update_one(self, data: Sheet):
        pass

    async def remove_many(self, data: list[Sheet]):
        pass
