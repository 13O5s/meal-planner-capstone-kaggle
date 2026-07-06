from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.recipe import (
    Recipe,
    RecipeTag,
    Tag,
)
from app.database.repositories.base import BaseRepository


class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Recipe)

    async def find_by_title(self, title: str) -> Recipe | None:
        return await self.find_one(title=title)

    async def get_active(self) -> Sequence[Recipe]:
        return await self.find(active=True)

    async def get_with_ingredients(
        self, recipe_id: str
    ) -> Recipe | None:
        result = await self._session.execute(
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(joinedload(Recipe.ingredients))
        )
        return result.unique().scalar_one_or_none()

    async def get_with_nutrition(
        self, recipe_id: str
    ) -> Recipe | None:
        result = await self._session.execute(
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(joinedload(Recipe.nutrition))
        )
        return result.unique().scalar_one_or_none()

    async def get_by_tag(self, tag_name: str) -> Sequence[Recipe]:
        result = await self._session.execute(
            select(Recipe)
            .join(RecipeTag)
            .join(Tag)
            .where(Tag.name == tag_name)
            .where(Recipe.active)
        )
        return result.unique().scalars().all()

    async def get_by_cuisine(self, cuisine: str) -> Sequence[Recipe]:
        return await self.find(cuisine=cuisine, active=True)

    async def get_by_difficulty(
        self, difficulty: str
    ) -> Sequence[Recipe]:
        return await self.find(difficulty=difficulty, active=True)

    async def search_by_title(
        self, query: str, limit: int = 10
    ) -> Sequence[Recipe]:
        result = await self._session.execute(
            select(Recipe)
            .where(Recipe.active)
            .where(Recipe.title.ilike(f"%{query}%"))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_or_create_tag(self, name: str) -> Tag:
        result = await self._session.execute(
            select(Tag).where(Tag.name == name)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            self._session.add(tag)
            await self._session.flush()
        return tag
