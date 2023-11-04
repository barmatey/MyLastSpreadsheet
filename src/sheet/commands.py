from typing import Iterable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.sheet import services, domain


class GetSheetById(BaseModel):
    id: UUID
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        return await self.receiver.get_sheet_by_id(self.id)


class CreateSheet(BaseModel):
    data: domain.Sheet
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        return await self.receiver.create_sheet(self.data)


class UpdateCells(BaseModel):
    data: Iterable[domain.Cell]
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> None:
        await self.receiver.cell_service.update_many(self.data)


class CreateFormula(BaseModel):
    parents: list[domain.Cell]
    target: domain.Cell
    formula_key: str
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Formula:
        formula = await self.receiver.formula_service.create_one(self.parents, self.target, self.formula_key)
        return formula


class CreateCheckerSheet(BaseModel):
    parent_sheet_id: UUID
    receiver: services.ReportSheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        return await self.receiver.create_checker_sheet(self.parent_sheet_id)
