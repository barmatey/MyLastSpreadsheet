from sqlalchemy.ext.asyncio import AsyncSession

from src.base.repo.repository import Repository
from . import services, domain
from .infrastructure import postgres, gateway, subfactory
from src.spreadsheet.bootstrap import Bootstrap as SheetBootstrap


class Bootstrap(SheetBootstrap):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._source_repo: services.SourceRepo = postgres.SourceFullRepo(session)
        self._group_repo: Repository[domain.Group] = postgres.GroupRepo(session)

    def get_source_service(self) -> services.SourceService:
        source_service = services.SourceService(repo=self._source_repo)
        return source_service

    def get_create_group_usecase(self) -> services.CreateGroupUsecase:
        usecase = services.CreateGroupUsecase(repo=self._group_repo, subfac=subfactory.ReportSubfac())
        return usecase
