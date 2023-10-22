from typing import Type
from uuid import UUID

from sqlalchemy import TIMESTAMP, func, select, update, delete, Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core import OrderBy
from ..entity import Entity
from ... import helpers
from src.base.repo.repository import Repository, T


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


class PostgresRepo(Repository):
    def __init__(self, session: AsyncSession, model: Type[Base]):
        self._model = model
        self._session = session

    async def add_many(self, data: list[T]):
        models = [self._model.from_entity(x) for x in data]
        self._session.add_all(models)

    async def get_one_by_id(self, uuid: UUID) -> T:
        stmt = select(self._model).where(self._model.id == uuid)
        models = list(await self._session.scalars(stmt))
        if len(models) != 1:
            raise LookupError(f"models count is {len(models)}")
        return models[0].to_entity()

    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None,
                       slice_from=None, slice_to=None) -> list[T]:
        stmt = select(self._model)
        if filter_by is not None:
            stmt = stmt.where(*helpers.postgres.parse_filter_by(self._model, filter_by))
        if order_by is not None:
            stmt = stmt.order_by(*helpers.postgres.parse_order_by(self._model, order_by))
        if slice_from is not None and slice_to is not None:
            stmt = stmt.slice(slice_from, slice_to)
        models = await self._session.execute(stmt)
        entities = [x.to_entity() for x in models.scalars()]
        return entities

    async def get_uniques(self, columns_by: list[str], filter_by: dict = None, order_by: OrderBy = None) -> Result:
        stmt = select(self._model).distinct(*[self._model.__table__.c[col] for col in columns_by])
        if filter_by is not None:
            stmt = stmt.where(*helpers.postgres.parse_filter_by(self._model, filter_by))
        if order_by is not None:
            stmt = stmt.order_by(*helpers.postgres.parse_order_by(self._model, order_by))
        result = await self._session.execute(stmt)
        return result

    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        stmt = select(self._model).where(self._model.id.in_(ids))
        result = await self._session.execute(stmt)
        entities = [x.to_entity() for x in result.scalars()]
        return entities

    async def update_one(self, data: T):
        model = self._model.from_entity(data)
        stmt = update(self._model).where(self._model.id == data.id).returning(self._model.id)
        result = await self._session.execute(stmt, model.__dict__)
        if len(list(result)) != 1:
            raise LookupError(f"{len(list(result))}")

    async def update_many(self, data: list[T]):
        stmt = update(self._model)
        data = [self._model.from_entity(x).__dict__ for x in data]
        await self._session.execute(stmt, data)

    async def remove_many(self, data: list[T]):
        ids = [x.id for x in data]
        stmt = delete(self._model).where(self._model.id.in_(ids)).returning(self._model.id)
        result = await self._session.execute(stmt)
        if len(list(result)) != len(data):
            raise LookupError
