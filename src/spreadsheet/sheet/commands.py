from uuid import UUID, uuid4

from pydantic import Field

from src.bus.eventbus import EventBus
from src.core import PydanticModel

from src.spreadsheet.cell import (
    entity as cell_entity,
)
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    services as sheet_services,
    bootstrap as sheet_bootstrap,
)


class CreateSheet(PydanticModel):
    bootstrap: sheet_bootstrap.Bootstrap
    table: list[list[cell_entity.CellValue]] | None = None
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self) -> sheet_entity.Sheet:
        table = self.table if self.table is not None else []
        sheet = await self.bootstrap.get_sheet_service().create_sheet(table)
        await self.bootstrap.get_event_bus().run()
        return sheet


class GetSheetByUuid(PydanticModel):
    uuid: UUID
    bootstrap: sheet_bootstrap.Bootstrap

    async def execute(self) -> sheet_entity.Sheet:
        return await self.bootstrap.get_sheet_service().get_sheet_by_uuid(self.uuid)

