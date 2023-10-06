from abc import abstractmethod, ABC
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src.helpers.decorators import singleton
from src.spreadsheet.cell.entity import Cell, CellValue, CellDtype
from src.spreadsheet.sheet.repository import Base


class CellRepo(ABC):
    @abstractmethod
    async def add(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    async def get_all(self) -> list[Cell]:
        raise NotImplemented

    @abstractmethod
    async def get_many(self, filter_by: dict, order_by: list[str] = None, asc=True):
        raise NotImplemented

    @abstractmethod
    async def get_one_by_uuid(self, uuid: UUID) -> Cell:
        raise NotImplemented

    @abstractmethod
    async def update_one(self, cell: Cell):
        raise NotImplemented

    @abstractmethod
    async def delete_one(self, cell: Cell):
        raise NotImplemented


@singleton
class CellRepoFake(CellRepo):
    def __init__(self):
        self._data: dict[UUID, Cell] = {}

    def get_all(self) -> list[Cell]:
        return list(self._data.values())

    def add(self, cell: Cell):
        if self._data.get(cell.uuid) is not None:
            raise Exception("already exist")
        self._data[cell.uuid] = cell.model_copy(deep=True)

    def get_many(self, filter_by: dict, order_by: list[str] = None, asc=True):
        result: list[Cell] = []
        for cell in self._data.values():
            if all([cell.__getattribute__(key) == value for key, value in filter_by.items()]):
                result.append(cell)
        return result

    def get_one_by_uuid(self, uuid: UUID) -> Cell:
        return self._data[uuid].model_copy(deep=True)

    def update_one(self, cell: Cell):
        if self._data.get(cell.uuid) is None:
            raise LookupError
        self._data[cell.uuid] = cell.model_copy(deep=True)

    def delete_one(self, cell: Cell):
        if self._data.get(cell.uuid) is None:
            raise LookupError
        del self._data[cell.uuid]

    def clear(self):
        self._data = {}


class CellModel(Base):
    __tablename__ = "cell"
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    dtype: Mapped[str] = mapped_column(String(8), nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    row_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("row_sindex.uuid"))
    col_sindex_uuid: Mapped[UUID] = mapped_column(ForeignKey("col_sindex.uuid"))


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
                          row_sindex_uuid=cell.row_sindex.uuid, col_sindex_uuid=cell.col_sindex.uuid)
        self._session.add(model)

    async def get_all(self) -> list[Cell]:
        raise NotImplemented

    async def get_many(self, filter_by: dict, order_by: list[str] = None, asc=True):
        raise NotImplemented

    async def get_one_by_uuid(self, uuid: UUID) -> Cell:
        raise NotImplemented

    async def update_one(self, cell: Cell):
        raise NotImplemented

    async def delete_one(self, cell: Cell):
        raise NotImplemented
