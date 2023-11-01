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





class InsertRows(BaseModel):
    id: UUID
    table: list[list[domain.CellValue]]
    before_sindex: domain.RowSindex
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.insert_sindexes(self.id, self.table, self.before_sindex)


class InsertCols(BaseModel):
    id: UUID
    table: list[list[domain.CellValue]]
    before_sindex: domain.ColSindex
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.insert_sindexes(self.id, self.table, self.before_sindex)
