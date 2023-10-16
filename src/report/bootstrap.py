from sqlalchemy.ext.asyncio import AsyncSession

from . import services, domain
from .infrastructure import postgres
from ..base.repo.repository import Repository


class Bootstrap:
    def __init__(self, session: AsyncSession):
        self._source_repo: services.SourceRepo = postgres.SourceFullRepo(session)

    def get_source_service(self) -> services.SourceService:
        source_service = services.SourceService(repo=self._source_repo)
        return source_service
