import pytest

import db
from src.report import bootstrap, commands


@pytest.mark.asyncio
async def test_create_source():
    async with db.get_async_session() as session:
        boot = bootstrap.Bootstrap(session)
        cmd = commands.CreateSource(title="Hello", receiver=boot.get_source_service())
        await cmd.execute()
        await session.commit()
