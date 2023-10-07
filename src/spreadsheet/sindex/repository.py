from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import String, Integer, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import helpers
from src.spreadsheet.sheet.entity import Sheet
from src.spreadsheet.sheet.repository import Base
from src.spreadsheet.sindex.entity import Sindex, SindexDirection


class SindexRepo(ABC):
    @abstractmethod
    async def add(self, sindex: Sindex):
        raise NotImplemented

    @abstractmethod
    async def get_sheet_rows(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    async def get_sheet_cols(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    async def get_all(self) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    async def get_many(self, direction: SindexDirection, filter_by: dict,
                       order_by: str | list[str] = None, asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    async def get_one_by_uuid(self, uuid: UUID) -> Sindex:
        raise NotImplemented

    @abstractmethod
    async def get_many_by_positions(self, sheet_uuid: UUID, positions: list[int],
                                    order_by: list[str] = None, asc=True) -> list[Sindex]:
        raise NotImplemented

    @abstractmethod
    async def update(self, sindex: Sindex):
        raise NotImplemented

    @abstractmethod
    async def remove(self, sindex: Sindex):
        raise NotImplemented

    @abstractmethod
    async def remove_many_by_position(self, sheet_uuid: UUID, positions: list[int]):
        raise NotImplemented

    @abstractmethod
    async def remove_many_by_uuid(self, uuids: list[UUID]):
        raise NotImplemented


class RowSindexModel(Base):
    __tablename__ = "row_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')

    def to_entity(self, sheet: Sheet) -> Sindex:
        return Sindex(sheet=sheet, direction="ROW", position=self.position)


class ColSindexModel(Base):
    __tablename__ = "col_sindex"
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_uuid: Mapped[UUID] = mapped_column(ForeignKey("sheet.uuid"))
    cells = relationship('CellModel')


class SindexRepoPostgres(SindexRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sindex: Sindex):
        if sindex.direction == "ROW":
            model = RowSindexModel
        elif sindex.direction == "COL":
            model = ColSindexModel
        else:
            raise ValueError
        model = model(uuid=sindex.uuid, position=sindex.position, sheet_uuid=sindex.sheet.uuid)
        self._session.add(model)

    async def get_sheet_rows(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[Sindex]:
        orders = helpers.postgres.parse_order_by(RowSindexModel, order_by, asc)
        stmt = select(RowSindexModel).where(RowSindexModel.sheet_uuid == sheet.uuid).order_by(*orders)
        result = await self._session.execute(stmt)
        result = [x.to_entity(sheet) for x in result.scalars().fetchall()]
        return result

    async def get_sheet_cols(self, sheet: Sheet, order_by: str | list[str] = 'position', asc=True) -> list[Sindex]:
        orders = helpers.postgres.parse_order_by(ColSindexModel, order_by, asc)
        stmt = select(ColSindexModel).where(ColSindexModel.sheet_uuid == sheet.uuid).order_by(*orders)
        result = await self._session.execute(stmt)
        result = [x.to_entity(sheet) for x in result.scalars().fetchall()]
        return result

    async def get_all(self) -> list[Sindex]:
        raise NotImplemented

    async def get_many(self, direction: SindexDirection, filter_by: dict,
                       order_by: str | list[str] = "position", asc=True) -> list[Sindex]:
        if direction == "ROW":
            model = RowSindexModel
        elif direction == "COL":
            model = ColSindexModel
        else:
            raise ValueError
        filters = [model.__table__.c[key] == value for key, value in filter_by.items()]
        orders = helpers.postgres.parse_order_by(model, order_by, asc)
        stmt = select(model).where(*filters).order_by(*orders)
        result = await self._session.execute(stmt)
        result = [x.to_entity() for x in result.scalars().fetchall()]
        return result

    async def get_one_by_uuid(self, uuid: UUID) -> Sindex:
        raise NotImplemented

    async def get_many_by_positions(self, sheet_uuid: UUID, positions: list[int], order_by: list[str] = None, asc=True):
        raise NotImplemented

    async def update(self, sindex: Sindex):
        raise NotImplemented

    async def remove(self, sindex: Sindex):
        raise NotImplemented

    async def remove_many_by_position(self, sheet_uuid: UUID, positions: list[int]):
        raise NotImplemented

    async def remove_many_by_uuid(self, uuids: list[UUID]):
        raise NotImplemented
