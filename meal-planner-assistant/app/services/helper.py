from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session, is_db_initialized


@asynccontextmanager
async def optional_session() -> AsyncIterator[AsyncSession | None]:
    if is_db_initialized():
        async with get_session() as session:
            yield session
    else:
        yield None
