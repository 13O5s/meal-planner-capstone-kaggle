"""Bridge between ADK tools and the database.

Tools use this adapter to read data. It tries the database first;
if the database is not initialized, it falls back to the in-memory stores.
"""

from __future__ import annotations

import asyncio

from app.data.stores import NUTRITION_DB, PRICE_DB, normalize_ingredient_name
from app.database.repositories import IngredientRepository
from app.database.session import _engine, get_session_factory

_ingredient_name_cache: dict[str, str] | None = None


def resolve_ingredient_name(raw: str) -> str:
    if _engine is not None:
        return _resolve_from_db(raw)
    return normalize_ingredient_name(raw)


def _resolve_from_db(raw: str) -> str:
    global _ingredient_name_cache
    if _ingredient_name_cache is None:

        async def _build():
            factory = get_session_factory()
            async with factory() as session:
                repo = IngredientRepository(session)
                all_ings = await repo.find(active=True)
                cache = {}
                for ing in all_ings:
                    cache[ing.name.lower()] = ing.name
                    aliases = await repo.get_aliases(str(ing.id))
                    for alias in aliases:
                        cache[alias.alias.lower()] = ing.name
                return cache

        _ingredient_name_cache = asyncio.run(_build())
    cleaned = raw.strip().lower()
    return _ingredient_name_cache.get(cleaned, cleaned)


def get_price_data(name: str) -> dict:
    if _engine is not None:

        async def _fetch():
            factory = get_session_factory()
            async with factory() as session:
                repo = IngredientRepository(session)
                ing = await repo.resolve_name(name)
                if ing is None:
                    return {}
                return {
                    "price_per_unit": 0,
                    "unit": ing.default_unit,
                    "category": ing.category or "unknown",
                }

        return asyncio.run(_fetch())
    return PRICE_DB.get(name, {})


def get_nutrition_data(name: str) -> dict:
    if _engine is not None:

        async def _fetch():
            factory = get_session_factory()
            async with factory() as session:
                repo = IngredientRepository(session)
                ing = await repo.resolve_name(name)
                if ing is None:
                    return {}
                nutrition = await repo.get_nutrition(str(ing.id))
                if nutrition is None:
                    return {}
                return {
                    "calories_per_100g": float(
                        nutrition.calories_per_100g
                    ),
                    "protein_per_100g": float(
                        nutrition.protein_per_100g
                    ),
                    "carbs_per_100g": float(
                        nutrition.carbohydrates_per_100g
                    ),
                    "fat_per_100g": float(nutrition.fat_per_100g),
                }

        return asyncio.run(_fetch())
    return NUTRITION_DB.get(name, {})


def get_known_ingredients() -> set[str]:
    if _engine is not None:

        async def _fetch():
            factory = get_session_factory()
            async with factory() as session:
                repo = IngredientRepository(session)
                all_ings = await repo.find(active=True)
                names = set()
                for ing in all_ings:
                    names.add(ing.name.lower())
                    aliases = await repo.get_aliases(str(ing.id))
                    for alias in aliases:
                        names.add(alias.alias.lower())
                return names

        return asyncio.run(_fetch())
    return set(NUTRITION_DB.keys()) | set(PRICE_DB.keys())
