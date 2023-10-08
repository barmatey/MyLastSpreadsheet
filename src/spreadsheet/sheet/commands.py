from uuid import UUID, uuid4

from pydantic import Field

from src.core import PydanticModel
from ..cell import entity as cell_entity
from . import (entity as sheet_entity, usecases as sheet_usecases, repository as sheet_repo)


class CreateSheet(PydanticModel):
    sheet_repo: sheet_repo.SheetRepo
    table: list[list[cell_entity.CellValue]] | None = None
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self) -> sheet_entity.Sheet:
        table = self.table if self.table is not None else []
        sheet = await sheet_usecases.create_sheet(table, self.sheet_repo)
        return sheet


class GetSheetByUuid(PydanticModel):
    uuid: UUID
    sheet_repo: sheet_repo.SheetRepo

    async def execute(self) -> sheet_entity.Sheet:
        sheet = await sheet_usecases.get_by_uuid(self.uuid, self.sheet_repo)
        return sheet
