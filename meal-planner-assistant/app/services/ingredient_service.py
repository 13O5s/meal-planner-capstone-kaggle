from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.stores import NUTRITION_DB, PRICE_DB, normalize_ingredient_name
from app.database.models.ingredient import Ingredient
from app.database.repositories import IngredientRepository


class IngredientService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._repo = IngredientRepository(session) if session else None
        self._session = session

    async def resolve_name(self, raw: str) -> str:
        if self._repo:
            ing = await self._repo.resolve_name(raw)
            if ing:
                return ing.name
        return normalize_ingredient_name(raw)

    async def get_price(self, name: str) -> dict:
        if self._repo:
            ing = await self._repo.resolve_name(name)
            if ing:
                return {
                    "price_per_unit": 0,
                    "unit": ing.default_unit or "piece",
                    "category": ing.category or "unknown",
                }
            return {}
        return PRICE_DB.get(name, {})

    async def get_nutrition(self, name: str) -> dict:
        if self._repo:
            ing = await self._repo.resolve_name(name)
            if ing is None:
                return {}
            nutrition = await self._repo.get_nutrition(str(ing.id))
            if nutrition is None:
                return {}
            return {
                "calories_per_100g": float(nutrition.calories_per_100g),
                "protein_per_100g": float(nutrition.protein_per_100g),
                "carbs_per_100g": float(nutrition.carbohydrates_per_100g),
                "fat_per_100g": float(nutrition.fat_per_100g),
            }
        return NUTRITION_DB.get(name, {})

    async def get_known_ingredients(self) -> set[str]:
        if self._repo:
            all_ings = await self._repo.find(active=True)
            names: set[str] = set()
            for ing in all_ings:
                names.add(ing.name.lower())
                aliases = await self._repo.get_aliases(str(ing.id))
                for alias in aliases:
                    names.add(alias.alias.lower())
            return names
        return set(NUTRITION_DB.keys()) | set(PRICE_DB.keys())

    async def find_all_active(self) -> Sequence[Ingredient]:
        if self._repo:
            return await self._repo.find(active=True)
        return []
