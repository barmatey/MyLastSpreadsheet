from abc import ABC
from uuid import UUID

from ..base.repo import repository
from src.spreadsheet import services as sheet_services
from . import domain as report_domain


class SourceRepo(ABC):
    @property
    def source_repo(self) -> repository.Repository[report_domain.Source]:
        raise NotImplemented

    @property
    def wire_repo(self) -> repository.Repository[report_domain.Wire]:
        raise NotImplemented


class SourceService:
    def __init__(self, repo: SourceRepo):
        self._repo = repo

    async def create_source(self, source: report_domain.Source):
        await self._repo.source_repo.add_many([source])

    async def get_source_by_id(self, uuid: UUID) -> report_domain.Source:
        return await self._repo.source_repo.get_one_by_id(uuid)

    async def append_wires(self, wires: list[report_domain.Wire]):
        await self._repo.wire_repo.add_many(wires)

