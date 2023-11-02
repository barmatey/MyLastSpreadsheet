from uuid import UUID
from fastapi import Depends, APIRouter

import db
from src import helpers

from .. import domain,  bootstrap, commands

router_sheet = APIRouter(
    prefix='/sheet',
    tags=['Sheet']
)


@router_sheet.get("/{sheet_id}")
@helpers.decorators.async_timeit
async def get_sheet(sheet_id: UUID, get_asession=Depends(db.get_async_session)) -> domain.Sheet:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSheetByUuid(uuid=sheet_id, receiver=boot.get_sheet_service())
        sheet = await cmd.execute()
        return sheet
