from loguru import logger
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = f"postgresql+asyncpg://postgres:145190hfp@127.0.0.1:5432/spreadsheet_db"


async_engine = create_async_engine(DATABASE_URL)


def async_session_generator():
    return sessionmaker(async_engine, class_=AsyncSession)


@asynccontextmanager
async def get_async_session() -> AsyncSession:
    try:
        async_session = async_session_generator()
        async with async_session() as session:
            logger.info(f"session created")
            yield session
    except Exception as err:
        err = str(err)
        if len(err) > 5_000:
            err = err[0:5_000]
        logger.error(err)
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.info(f"session closed")
