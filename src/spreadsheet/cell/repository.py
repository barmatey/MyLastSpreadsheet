from abc import abstractmethod, ABC
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, ForeignKey, delete, select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src import helpers
from src.core import OrderBy
from src.spreadsheet.cell.entity import Cell, CellValue, CellDtype
from src.spreadsheet.sheet_meta.entity import SheetMeta
from src.spreadsheet.sheet_meta.repository import Base
from src.spreadsheet.sindex.entity import RowSindex, ColSindex
from src.spreadsheet.sindex.repository import RowSindexModel, ColSindexModel


class CellRepo(ABC):
    @abstractmethod
    async def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    async def add_many(self, cells: list[Cell]):
        raise NotImplemented

    @abstractmethod
    async def get_many_by_sheet_filters(self, sheet: SheetMeta, rows: list[RowSindex] = None,
                                        cols: list[ColSindex] = None,
                                        order_by: OrderBy = None) -> list[Cell]:
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, cells: list[Cell]):
        raise NotImplemented


class CellModel(Base):
    __tablename__ = "cell"
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    dtype: Mapped[str] = mapped_column(String(8), nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    row_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("row_sindex.uuid"))
    col_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("col_sindex.uuid"))

    def to_entity(self, sheet: SheetMeta, row: RowSindex, col: ColSindex):
        return Cell(sheet=sheet, row_sindex=row, col_sindex=col, value=get_value(self.value, self.dtype),
                    uuid=self.uuid)


def get_value(value: str, dtype: CellDtype) -> CellValue:
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


def get_dtype(value: CellValue) -> CellDtype:
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


class CellRepoPostgres(CellRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, cell: Cell):
        model = CellModel(uuid=cell.uuid, value=str(cell.value), dtype=get_dtype(cell.value),
                          row_sindex_uuid=cell.row_sindex.uuid, col_sindex_uuid=cell.col_sindex.uuid,
                          sheet_uuid=cell.sheet.uuid)
        self._session.add(model)

    async def add_many(self, cells: list[Cell]):
        data = [{
            "uuid": x.uuid,
            "value": str(x.value),
            "dtype": get_dtype(x.value),
            "row_sindex_uuid": x.row_sindex.uuid,
            "col_sindex_uuid": x.col_sindex.uuid,
            "sheet_uuid": x.sheet.uuid,
        } for x in cells]
        stmt = insert(CellModel)
        await self._session.execute(stmt, data)

    async def get_many_by_sheet_filters(self, sheet: SheetMeta, rows: list[RowSindex] = None,
                                        cols: list[ColSindex] = None,
                                        order_by: OrderBy = None) -> list[Cell]:
        stmt = (
            select(CellModel, RowSindexModel, ColSindexModel)
            .join(RowSindexModel, CellModel.row_sindex_uuid == RowSindexModel.uuid)
            .join(ColSindexModel, CellModel.col_sindex_uuid == ColSindexModel.uuid)
            .where(CellModel.sheet_uuid == sheet.uuid)
        )
        if rows:
            stmt = stmt.where(CellModel.row_sindex_uuid.in_([x.uuid for x in rows]))
        if cols:
            stmt = stmt.where(CellModel.col_sindex_uuid.in_([x.uuid for x in cols]))
        if order_by:
            orders = helpers.postgres.parse_order_by(CellModel, *order_by)
            stmt = stmt.order_by(*orders)

        result = await self._session.execute(stmt)
        result = [x[0].to_entity(sheet, row=x[1].to_entity(sheet), col=x[2].to_entity(sheet)) for x in result]
        return result

    async def remove_many(self, cells: list[Cell]):
        uuids = [x.uuid for x in cells]
        stmt = delete(CellModel).where(CellModel.uuid.in_(uuids))
        await self._session.execute(stmt)
