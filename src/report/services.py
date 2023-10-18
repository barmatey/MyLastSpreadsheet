from abc import ABC, abstractmethod
from uuid import UUID
from src.base.repo import repository

from . import domain, subscriber


class SourceRepo(ABC):
    @property
    def source_info_repo(self) -> repository.Repository[domain.SourceInfo]:
        raise NotImplemented

    @property
    def wire_repo(self) -> repository.Repository[domain.Wire]:
        raise NotImplemented

    @abstractmethod
    async def add_source(self, source: domain.Source):
        raise NotImplemented

    @abstractmethod
    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        raise NotImplemented


class SourceService:
    def __init__(self, repo: SourceRepo):
        self._repo = repo

    async def create_source(self, source: domain.Source):
        await self._repo.add_source(source)

    async def get_source_by_id(self, uuid: UUID) -> domain.Source:
        return await self._repo.get_source_by_id(uuid)

    async def append_wires(self, wires: list[domain.Wire]):
        await self._repo.wire_repo.add_many(wires)


class CreateGroupUsecase:
    def __init__(self, repo: repository.Repository[domain.Group], subfac: subscriber.SubscriberFactory):
        self._repo = repo
        self._subfac = subfac

    async def execute(self, title: str, source: domain.Source, ccols: list[domain.Ccol]) -> domain.Group:
        plan_items = domain.PlanItems(ccols=ccols)
        await self._subfac.create_source_subscriber(plan_items).follow_source(source)
        group = domain.Group(title=title, plan_items=plan_items, source_info=source.source_info)
        await self._repo.add_many([group])
        return group
