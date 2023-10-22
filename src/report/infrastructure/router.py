from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

import db
from .. import bootstrap, commands, domain
from ...core import OrderBy

router_source = APIRouter(
    prefix="/source",
    tags=["Source"],
)


@router_source.post("/")
async def create_source(title: str, get_asession=Depends(db.get_async_session)) -> domain.SourceInfo:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSource(title=title, receiver=boot.get_source_service())
        source = await cmd.execute()
        return source.source_info


@router_source.get("/")
async def get_sources(get_asession=Depends(db.get_async_session)) -> list[domain.SourceInfo]:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSourceInfoList(receiver=boot.get_source_service())
        result = await cmd.execute()
        return result


@router_source.get("/{source_id}")
async def get_source(source_id: UUID, get_asession=Depends(db.get_async_session)) -> domain.SourceInfo:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSourceInfoById(id=source_id, receiver=boot.get_source_service())
        result = await cmd.execute()
        return result


@router_source.get("/{source_id}/plan-items")
async def get_plan_items(source_id: UUID, get_asession=Depends(db.get_async_session)):
    raise NotImplemented


router_wire = APIRouter(
    prefix="/wire",
    tags=["Wire"]
)


@router_wire.get("/")
async def get_many(source_id: UUID,
                   date: datetime = None,
                   sender: float = None,
                   receiver: float = None,
                   debit: float = None,
                   credit: float = None,
                   subconto_first: str = None,
                   subconto_second: str = None,
                   comment: str = None,
                   paginate_from: int = None,
                   paginate_to: int = None,
                   order_by: str = 'date',
                   asc: bool = False,
                   get_asession=Depends(db.get_async_session)) -> list[domain.Wire]:
    filter_by = {
        "source_id": source_id,
        "date": date,
        "sender": sender,
        "receiver": receiver,
        "sub1": subconto_first,
        "sub2": subconto_second,
    }
    filter_by = {key: value for key, value in filter_by.items() if value is not None}
    order_by = OrderBy(order_by, asc)
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetWires(filter_by=filter_by, order_by=order_by, slice_from=paginate_from, slice_to=paginate_to,
                                receiver=boot.get_source_service())
        wires = await cmd.execute()
        return wires


router_report = APIRouter(
    prefix="/report",
    tags=['Report']
)


@router_report.post("/")
async def create_report(get_asession=Depends(db.get_async_session)):
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
