from uuid import UUID, uuid4

from pydantic import Field

from src.core import PydanticModel
from ..cell import entity as cell_entity
from . import (entity as sheet_entity, usecases as sheet_usecases, events as sheet_events)
from ...bus.eventbus import EventBus, Queue


class CreateSheet(PydanticModel):
    bus: EventBus
    table: list[list[cell_entity.CellValue]] | None = None
    uuid: UUID = Field(default_factory=uuid4)

    async def execute(self) -> sheet_entity.Sheet:
        table = self.table if self.table is not None else []
        sheet = await sheet_usecases.create_sheet(table)
        await self.bus.run()
        return sheet


class GetSheetByUuid(PydanticModel):
    uuid: UUID
    bus: EventBus

    async def execute(self) -> sheet_entity.Sheet:
        Queue().append(sheet_events.SheetRequested(uuid=self.uuid))
        await self.bus.run()
        sheet = self.bus.results[self.uuid]
        return sheet
