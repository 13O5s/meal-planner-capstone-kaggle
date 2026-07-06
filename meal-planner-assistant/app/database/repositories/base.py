from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def create(self, **kwargs: Any) -> ModelT:
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def get(self, id: uuid.UUID) -> ModelT | None:
        return await self._session.get(self._model, id)

    async def find(self, **filters: Any) -> Sequence[ModelT]:
        stmt = select(self._model)
        for col, val in filters.items():
            if hasattr(self._model, col):
                stmt = stmt.where(getattr(self._model, col) == val)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def find_one(self, **filters: Any) -> ModelT | None:
        stmt = select(self._model)
        for col, val in filters.items():
            if hasattr(self._model, col):
                stmt = stmt.where(getattr(self._model, col) == val)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def update(self, id: uuid.UUID, **values: Any) -> ModelT | None:
        stmt = (
            sa_update(self._model)
            .where(self._model.id == id)
            .values(**values)
            .returning(self._model)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: uuid.UUID) -> bool:
        stmt = sa_delete(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def count(self, **filters: Any) -> int:
        stmt = select(self._model)
        for col, val in filters.items():
            if hasattr(self._model, col):
                stmt = stmt.where(getattr(self._model, col) == val)
        result = await self._session.execute(
            stmt.with_only_columns(self._model.id)
        )
        return len(result.all())
