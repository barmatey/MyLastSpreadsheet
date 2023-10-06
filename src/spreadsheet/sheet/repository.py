from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import TIMESTAMP, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .entity import Sheet
from ...helpers.decorators import singleton


class SheetRepo(ABC):
    @abstractmethod
    async def add(self, sheet: Sheet):
        raise NotImplemented

    @abstractmethod
    def update(self, sheet: Sheet):
        raise NotImplemented

    @abstractmethod
    def get_one_by_uuid(self, uuid: UUID) -> Sheet:
        raise NotImplemented

    @abstractmethod
    def remove_one(self, sheet: Sheet):
        raise NotImplemented


@singleton
class SheetRepoFake(SheetRepo):
    def __init__(self):
        self._data: dict[UUID, Sheet] = {}

    def add(self, sheet: Sheet):
        if self._data.get(sheet.uuid) is not None:
            raise Exception("already exist")
        self._data[sheet.uuid] = sheet.model_copy(deep=True)

    def get_one_by_uuid(self, uuid: UUID) -> Sheet:
        return self._data[uuid].model_copy(deep=True)

    def update(self, sheet: Sheet):
        if self._data.get(sheet.uuid) is None:
            raise LookupError
        self._data[sheet.uuid] = sheet.model_copy(deep=True)

    def remove_one(self, sheet: Sheet):
        del self._data[sheet.uuid]

    def clear(self):
        self._data = {}


class Base(DeclarativeBase):
    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())


class SheetModel(Base):
    __tablename__ = "sheet"
    row_size: Mapped[int] = mapped_column(Integer, nullable=False)
    col_size: Mapped[int] = mapped_column(Integer, nullable=False)


class SheetRepoPostgres(SheetRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, sheet: Sheet):
        model = SheetModel(uuid=sheet.uuid, row_size=sheet.size[0], col_size=sheet.size[1])
        self._session.add(model)

    def update(self, sheet: Sheet):
        raise NotImplemented

    def get_one_by_uuid(self, uuid: UUID) -> Sheet:
        raise NotImplemented

    def remove_one(self, sheet: Sheet):
        raise NotImplemented
