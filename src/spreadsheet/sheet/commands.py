from uuid import UUID, uuid4

from pydantic import Field

from src.core import PydanticModel
from ..cell import entity as cell_entity, events as cell_events, usecases as cell_usecases, repository as cell_repo
from ..sindex import (entity as sindex_entity, events as sindex_events, usecases as sindex_usecases, repository as sindex_repo)
from ..sheet_info import (entity as sm_entity, events as sm_events, usecases as sm_usecases, repository as sm_repo)
from . import (entity as sheet_entity, usecases as sheet_usecases, repository as sheet_repo)


class CreateSheet(PydanticModel):
    table: list[list[cell_entity.CellValue]]
    sheet_repo: sheet_repo.SheetRepo
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self) -> sheet_entity.Sheet:
        sheet = await sheet_usecases.create_sheet(self.table, self.sheet_repo)
        return sheet
