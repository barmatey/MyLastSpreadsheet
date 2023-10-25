from datetime import datetime
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger

import db
from . import schema
from .. import bootstrap, commands, domain
from ... import helpers
from ...core import OrderBy

router_source = APIRouter(
    prefix="/source",
    tags=["Source"],
)


@router_source.post("/")
async def create_source(sf: domain.SourceInfo, get_asession=Depends(db.get_async_session)) -> domain.SourceInfo:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSource(title=sf.title, receiver=boot.get_source_service())
        source = await cmd.execute()
        await session.commit()
        return source.source_info


@router_source.get("/")
async def get_sources(get_asession=Depends(db.get_async_session)) -> list[domain.SourceInfo]:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSourceInfoList(receiver=boot.get_source_service())
        result = await cmd.execute()
        return result


@router_source.delete("/{source_id}")
async def delete_source(source_id: UUID, get_asession=Depends(db.get_async_session)) -> int:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.DeleteSourceById(id=source_id, receiver=boot.get_source_service())
        await cmd.execute()
        await boot.get_event_bus().run()
        await session.commit()
        return 1


@router_source.get("/{source_id}")
async def get_source(source_id: UUID, get_asession=Depends(db.get_async_session)) -> domain.SourceInfo:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetSourceInfoById(id=source_id, receiver=boot.get_source_service())
        result = await cmd.execute()
        return result


@router_source.get("/{source_id}/plan-items")
async def get_plan_items(source_id: UUID, get_asession=Depends(db.get_async_session)) -> list[domain.Wire]:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetUniqueWires(fields=["sender", "receiver", "sub1", "sub2"],
                                      source_id=source_id, receiver=boot.get_source_service())
        result = await cmd.execute()
        return result


router_wire = APIRouter(
    prefix="/wire",
    tags=["Wire"]
)


@router_wire.post("/{source_id}/csv")
async def create_many_from_csv(source_id: UUID, file: UploadFile, get_asession=Depends(db.get_async_session)) -> int:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        source_info = await commands.GetSourceInfoById(id=source_id, receiver=boot.get_source_service()).execute()

        df = pd.read_csv(file.file, parse_dates=['date'])
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df['amount'] = df['debit'] - df['credit']
        df = df[['sender', 'receiver', 'sub1', 'sub2', 'date', 'amount']]
        wires = [domain.Wire(**x, source_info=source_info) for x in df.to_dict(orient='records')]
        cmd = commands.AppendWires(wires=wires, source_info=source_info, receiver=boot.get_source_service())
        await cmd.execute()
        await session.commit()
        return 1


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
@helpers.decorators.async_timeit
async def create_report(data: schema.ReportCreateSchema,
                        get_asession=Depends(db.get_async_session)) -> domain.Report:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        source = await commands.GetSourceById(id=data.source_id, receiver=boot.get_source_service()).execute()
        cmd = commands.CreateReport(
            title=data.title,
            interval=data.interval.to_interval(),
            plan_items=domain.PlanItems(ccols=data.ccols),
            source=source,
            receiver=boot.get_report_service(),
        )
        report = await cmd.execute()
        await session.commit()
        return report


@router_report.get("/")
async def get_reports(get_asession=Depends(db.get_async_session)) -> list[schema.ReportRetrieveSchema]:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetReportList(receiver=boot.get_report_service())
        reports = await cmd.execute()
        return [schema.ReportRetrieveSchema.from_entity(x) for x in reports]


@router_report.get("/{report_id}")
async def get_report(report_id: UUID, get_asession=Depends(db.get_async_session)) -> schema.ReportRetrieveSchema:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.GetReportById(id=report_id, receiver=boot.get_report_service())
        report = await cmd.execute()
        return schema.ReportRetrieveSchema.from_entity(report)


@router_report.delete("/{report_id}")
async def delete_report(report_id: UUID, get_asession=Depends(db.get_async_session)) -> int:
    async with get_asession as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.DeleteReportById(id=report_id, receiver=boot.get_report_service())
        await cmd.execute()
        bus = boot.get_event_bus()
        await bus.run()
        await session.commit()
        return 1

