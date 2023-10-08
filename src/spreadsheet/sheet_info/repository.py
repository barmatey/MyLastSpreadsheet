from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import Integer, select, TIMESTAMP, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship

from .entity import SheetMeta
from ...helpers.decorators import singleton


class SheetMetaRepo(ABC):
    @abstractmethod
    async def add(self, sheet: SheetMeta):
        raise NotImplemented

    @abstractmethod
    async def update(self, sheet: SheetMeta):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID) -> SheetMeta:
        raise NotImplemented

    @abstractmethod
    def remove_one(self, sheet: SheetMeta):
        raise NotImplemented


class Base(DeclarativeBase):
    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"{self.__class__.__name__}"


class SheetInfoModel(Base):
    __tablename__ = "sheet"
    row_size: Mapped[int] = mapped_column(Integer, nullable=False)
    col_size: Mapped[int] = mapped_column(Integer, nullable=False)
    row_sindexes = relationship('RowSindexModel')
    col_sindexes = relationship('ColSindexModel')
    cells = relationship('CellModel')

    def to_entity(self) -> SheetMeta:
        return SheetMeta(uuid=self.uuid, size=(self.row_size, self.col_size))


class SheetInfoRepoPostgres(SheetMetaRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sheet: SheetMeta):
        model = SheetInfoModel(uuid=sheet.uuid, row_size=sheet.size[0], col_size=sheet.size[1])
        self._session.add(model)

    async def update(self, sheet: SheetMeta):
        stmt = select(SheetInfoModel).where(SheetInfoModel.uuid == sheet.uuid)
        model = await self._session.scalar(stmt)
        model.row_size = sheet.size[0]
        model.col_size = sheet.size[1]

    async def get_one_by_uuid(self, uuid: UUID) -> SheetMeta:
        stmt = select(SheetInfoModel).where(SheetInfoModel.uuid == uuid)
        model = await self._session.scalar(stmt)
        return model.to_entity()

    def remove_one(self, sheet: SheetMeta):
        raise NotImplemented
