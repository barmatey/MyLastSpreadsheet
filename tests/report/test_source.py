import random
from datetime import datetime

import pytest
from loguru import logger

import db
from src.report import bootstrap, commands, domain
from src.spreadsheet import commands as sheet_commands


async def create_source():
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSource(title="Hello", receiver=boot.get_source_service())
        source = await cmd.execute()
        await session.commit()
        return source


async def append_wires(source: domain.Source) -> domain.Source:
    wires = [
        domain.Wire(
            sender=i,
            receiver=i,
            amount=random.randrange(0, 111),
            sub1="first" if i % 2 == 0 else "second",
            sub2="no_info",
            date=datetime.now(),
            source_info=source.source_info,
        ) for i in range(0, 5)
    ]
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        await boot.get_source_service().append_wires(wires)
        await session.commit()

    source = source.model_copy(deep=True)
    source.wires = wires
    return source


@pytest.mark.asyncio
async def test_create_source():
    source = await create_source()
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        source = await commands.GetSourceById(id=source.source_info.id, receiver=boot.get_source_service()).execute()
        assert source.source_info.title == "Hello"


@pytest.mark.asyncio
async def test_append_wires():
    source = await create_source()
    await append_wires(source)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        source = await commands.GetSourceById(id=source.source_info.id, receiver=boot.get_source_service()).execute()
        assert len(source.wires) == 5


@pytest.mark.asyncio
async def test_create_group():
    source = await create_source()
    source = await append_wires(source)

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_create_group_usecase()
        group = await commands.CreateGroup(title="Group", source=source, receiver=receiver,
                                           ccols=['sender', 'sub1']).execute()
        await session.commit()

    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        receiver = boot.get_sheet_service()
        sheet = await sheet_commands.GetSheetByUuid(receiver=receiver, uuid=group.sheet_info.id).execute()
        logger.debug(f"\n{sheet.as_table()}")
