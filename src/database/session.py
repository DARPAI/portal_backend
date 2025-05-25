from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from src.errors import FastApiError
from src.errors import InternalError
from src.logger import logger
from src.settings import settings


database_url = f"{settings.PG_USER}:{settings.PG_PASSWORD}@{settings.PG_HOST}/{settings.PG_DB}"
database_url_sync = f"postgresql+psycopg2://{database_url}"
database_url_async = f"postgresql+asyncpg://{database_url}"


async_engine = create_async_engine(
    database_url_async,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    session = session_maker()
    try:
        yield session
        await session.commit()
    except FastApiError as e:
        await session.rollback()
        raise e
    except Exception as e:
        logger.error(f"There was an error while processing a request:\n{e}")
        await session.rollback()
        raise
    finally:
        await session.close()


# Needed because get_session commits at generator creation
async def manage_stream_session(stream: AsyncGenerator, session: AsyncSession) -> AsyncGenerator:
    try:
        async for chunk in stream:
            yield chunk
        await session.commit()
    except FastApiError as e:
        await session.rollback()
        raise e
    except Exception as e:
        logger.error(f"There was an error while processing a request:\n{e}")
        await session.rollback()
        raise InternalError("Something went wrong")
    finally:
        await session.close()
