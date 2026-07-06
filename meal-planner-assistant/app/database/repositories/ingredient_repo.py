from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.ingredient import (
    Ingredient,
    IngredientAlias,
    IngredientNutrition,
)
from app.database.repositories.base import BaseRepository


class IngredientRepository(BaseRepository[Ingredient]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Ingredient)

    async def find_by_name(self, name: str) -> Ingredient | None:
        return await self.find_one(name=name)

    async def find_by_alias(self, alias: str) -> Ingredient | None:
        result = await self._session.execute(
            select(IngredientAlias)
            .where(IngredientAlias.alias == alias)
            .options(joinedload(IngredientAlias.ingredient))
        )
        alias_record = result.scalar_one_or_none()
        return alias_record.ingredient if alias_record else None

    async def resolve_name(self, raw_name: str) -> Ingredient | None:
        ingredient = await self.find_by_name(raw_name)
        if ingredient:
            return ingredient
        return await self.find_by_alias(raw_name)

    async def get_aliases(
        self, ingredient_id: str
    ) -> Sequence[IngredientAlias]:
        result = await self._session.execute(
            select(IngredientAlias).where(
                IngredientAlias.ingredient_id == ingredient_id
            )
        )
        return result.scalars().all()

    async def get_nutrition(
        self, ingredient_id: str
    ) -> IngredientNutrition | None:
        result = await self._session.execute(
            select(IngredientNutrition).where(
                IngredientNutrition.ingredient_id == ingredient_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_category(
        self, category: str
    ) -> Sequence[Ingredient]:
        return await self.find(active=True, category=category)

    async def get_seasonal(self) -> Sequence[Ingredient]:
        return await self.find(seasonal=True, active=True)

    async def bulk_upsert_aliases(
        self, ingredient_id: str, aliases: list[str]
    ) -> None:
        existing = await self.get_aliases(ingredient_id)
        existing_set = {a.alias for a in existing}
        for alias in aliases:
            if alias not in existing_set:
                self._session.add(
                    IngredientAlias(
                        ingredient_id=ingredient_id, alias=alias
                    )
                )
        await self._session.flush()
