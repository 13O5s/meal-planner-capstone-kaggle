from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.config import get_config

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def is_db_initialized() -> bool:
    return _engine is not None


def init_db(url: str | None = None) -> None:
    global _engine, _session_factory
    if _engine is not None:
        return
    config = get_config()
    database_url = url or config.async_url
    _engine = create_async_engine(
        database_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
    )
    _session_factory = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    return _session_factory


@contextlib.asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
