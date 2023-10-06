import db

get_asession = db.get_async_session


async def create_sheet():
    async with get_asession as session:
        pass
