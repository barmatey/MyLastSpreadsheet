from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from src.core import OrderBy

T = TypeVar("T", bound=BaseModel)


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add_many(self, data: list[T]):
        raise NotImplemented

    @abstractmethod
    async def get_one_by_id(self, uuid: UUID) -> T:
        raise NotImplemented

    @abstractmethod
    async def get_many(self, filter_by: dict = None, order_by: OrderBy = None, slice_from=None, slice_to=None) -> list[T]:
        raise NotImplemented

    @abstractmethod
    async def get_many_by_id(self, ids: list[UUID], order_by: OrderBy = None) -> list[T]:
        raise NotImplemented

    @abstractmethod
    async def update_many(self, data: list[T]):
        raise NotImplemented

    @abstractmethod
    async def update_one(self, data: T):
        raise NotImplemented

    @abstractmethod
    async def remove_many(self, data: list[T]):
        raise NotImplemented

