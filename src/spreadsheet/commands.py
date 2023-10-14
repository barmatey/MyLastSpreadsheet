from uuid import UUID, uuid4

from pydantic import Field, BaseModel, ConfigDict

from . import domain, services


class CreateSheet(BaseModel):
    receiver: services.SheetService
    table: list[list[domain.CellValue]] | None = None
    uuid: UUID = Field(default_factory=uuid4)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        table = self.table if self.table is not None else []
        sheet = await self.receiver.create_sheet(table)
        return sheet


class GetSheetByUuid(BaseModel):
    uuid: UUID
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        return await self.receiver.get_sheet_by_uuid(self.uuid)
