from sqlalchemy.ext.asyncio import AsyncSession

from src.base.repo.repository import Repository
from . import services, domain
from .infrastructure import postgres, gateway, subfactory
from src.spreadsheet.bootstrap import Bootstrap as SheetBootstrap
from .infrastructure.gateway import SheetGatewayAPI


class Bootstrap(SheetBootstrap):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._source_repo: services.SourceRepo = postgres.SourceFullRepo(session)
        self._group_repo: Repository[domain.Group] = postgres.GroupRepo(session)
        self._report_repo: Repository[domain.Report] = postgres.ReportRepo(session)

    def get_source_service(self) -> services.SourceService:
        source_service = services.SourceService(repo=self._source_repo, queue=self._queue)
        return source_service

    def get_group_service(self) -> services.GroupService:
        usecase = services.GroupService(repo=self._group_repo, subfac=subfactory.ReportSubfac())
        return usecase

    def get_report_service(self) -> services.ReportService:
        sheet_service = self.get_sheet_service()
        gw = SheetGatewayAPI(sheet_service=sheet_service)
        return services.ReportService(self._report_repo, gw)
