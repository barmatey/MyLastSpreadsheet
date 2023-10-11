from abc import ABC, abstractmethod
from uuid import UUID

from loguru import logger
from sqlalchemy import Integer, select, TIMESTAMP, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship

from .entity import SheetInfo
from ...helpers.decorators import singleton


class SheetInfoRepo(ABC):
    @abstractmethod
    async def add(self, sheet: SheetInfo):
        raise NotImplemented

    @abstractmethod
    async def update(self, sheet: SheetInfo):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID) -> SheetInfo:
        raise NotImplemented

    @abstractmethod
    def remove_one(self, sheet: SheetInfo):
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

    def to_entity(self) -> SheetInfo:
        return SheetInfo(uuid=self.uuid, size=(self.row_size, self.col_size))


class SheetInfoRepoPostgres(SheetInfoRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sheet: SheetInfo):
        model = SheetInfoModel(uuid=sheet.uuid, row_size=sheet.size[0], col_size=sheet.size[1])
        self._session.add(model)

    async def update(self, sf: SheetInfo):
        stmt = update(SheetInfoModel).where(SheetInfoModel.uuid == sf.uuid).returning(SheetInfoModel.uuid)
        data = {
            "row_size": sf.size[0],
            "col_size": sf.size[1],
        }
        result = list(await self._session.execute(stmt, data))
        if len(result) != 1:
            raise LookupError(f"{result}")

    async def get_one_by_uuid(self, uuid: UUID) -> SheetInfo:
        stmt = select(SheetInfoModel).where(SheetInfoModel.uuid == uuid)
        model = await self._session.scalar(stmt)
        return model.to_entity()

    def remove_one(self, sheet: SheetInfo):
        raise NotImplemented
