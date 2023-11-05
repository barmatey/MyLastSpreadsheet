from uuid import UUID
from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse

import db
from src import helpers

from .. import domain,  bootstrap, commands
from . import schema

router_sheet = APIRouter(
    prefix='/sheet',
    tags=['Sheet']
)


@router_sheet.get("/{sheet_id}")
@helpers.decorators.async_timeit
async def get_sheet(sheet_id: UUID, get_asession=Depends(db.get_async_session)) -> schema.SheetSchema:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSheetById(id=sheet_id, receiver=boot.get_sheet_service())
        sheet = await cmd.execute()
        return schema.SheetSchema.from_sheet(sheet)


router_cell = APIRouter(
    prefix="/cell",
    tags=["Cell"],
)


@router_cell.patch("/{cell_id}")
@helpers.decorators.async_timeit
async def update_cell(cell: domain.Cell, get_asession=Depends(db.get_async_session)) -> domain.Cell:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.UpdateCells(data=[cell], receiver=boot.get_sheet_service())
        await cmd.execute()
        await boot.get_event_bus().run()
        await session.commit()
        return cell


@router_cell.patch("/")
async def update_cells(data: list[domain.Cell], get_asession=Depends(db.get_async_session)) -> int:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.UpdateCells(data=data, receiver=boot.get_sheet_service())
        await cmd.execute()
        await session.commit()
        return 1
