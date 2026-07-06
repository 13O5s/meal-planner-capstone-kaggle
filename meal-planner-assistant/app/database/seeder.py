"""Seed the database with canonical reference data from the existing in-memory stores.

Run during FastAPI startup if the database tables are empty.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.stores import (
    NUTRITION_DB,
    PRICE_DB,
    RECIPES,
    normalize_ingredient_name,
)
from app.database.models.ingredient import (
    Ingredient,
    IngredientAlias,
    IngredientNutrition,
)
from app.database.models.recipe import (
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeTag,
    Tag,
)

_ALIAS_MAP: dict[str, str] = {
    "breast": "chicken breast",
    "chicken": "chicken breast",
    "beef": "ground beef",
    "spaghetti": "pasta",
    "noodles": "pasta",
    "egg": "eggs",
    "cucumbers": "cucumber",
    "tomatoes": "tomato",
    "onions": "onion",
    "garlic clove": "garlic",
    "cloves garlic": "garlic",
    "bell peppers": "bell pepper",
    "red bell pepper": "bell pepper",
    "green bell pepper": "bell pepper",
    "carrots": "carrot",
    "broccoli florets": "broccoli",
    "olive oil spray": "olive oil",
    "milk 2%": "milk",
    "whole milk": "milk",
}

_NUTRITION_DB_EXTENDED: dict[str, dict] = {
    k: {
        "calories_per_100g": float(
            v.get(
                "calories_per_100g",
                v.get(
                    "calories_per_piece",
                    v.get("calories_per_100ml", 0),
                ),
            )
        ),
        "protein_per_100g": float(
            v.get(
                "protein_per_100g",
                v.get(
                    "protein_per_piece",
                    v.get("protein_per_100ml", 0),
                ),
            )
        ),
        "carbohydrates_per_100g": float(
            v.get(
                "carbs_per_100g",
                v.get(
                    "carbs_per_piece",
                    v.get("carbs_per_100ml", 0),
                ),
            )
        ),
        "fat_per_100g": float(
            v.get(
                "fat_per_100g",
                v.get("fat_per_piece", v.get("fat_per_100ml", 0)),
            )
        ),
    }
    for k, v in NUTRITION_DB.items()
}

_PRICE_DB_MAP: dict[str, dict] = {
    k.lower().strip(): v for k, v in PRICE_DB.items()
}

_RECIPE_DATA = list(RECIPES.values())


async def seed_ingredients(session: AsyncSession) -> None:
    result = await session.execute(select(Ingredient).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    all_names = set()
    all_names.update(_NUTRITION_DB_EXTENDED.keys())
    all_names.update(_PRICE_DB_MAP.keys())
    for recipe in _RECIPE_DATA:
        for ingredient in recipe.get("ingredients", []):
            all_names.add(
                normalize_ingredient_name(
                    ingredient["name"].lower().strip()
                )
            )

    for name in sorted(all_names):
        price_info = _PRICE_DB_MAP.get(name, {})
        category = price_info.get("category")
        default_unit = _NUTRITION_DB_EXTENDED.get(name, {}).get(
            "unit"
        ) or price_info.get("unit", "g")

        ingredient = Ingredient(
            name=name,
            category=category,
            default_unit=default_unit,
            seasonal=False,
            active=True,
        )
        session.add(ingredient)
    await session.flush()

    result = await session.execute(select(Ingredient))
    ingredients = result.scalars().all()
    ing_map: dict[str, Ingredient] = {i.name: i for i in ingredients}

    for alias_name, canonical in _ALIAS_MAP.items():
        target = ing_map.get(canonical)
        if target and alias_name != target.name:
            session.add(
                IngredientAlias(ingredient_id=target.id, alias=alias_name)
            )

    for name, nutrition in _NUTRITION_DB_EXTENDED.items():
        ing = ing_map.get(name)
        if ing:
            session.add(
                IngredientNutrition(
                    ingredient_id=ing.id,
                    calories_per_100g=nutrition.get(
                        "calories_per_100g", 0
                    ),
                    protein_per_100g=nutrition.get(
                        "protein_per_100g", 0
                    ),
                    carbohydrates_per_100g=nutrition.get(
                        "carbohydrates_per_100g", 0
                    ),
                    fat_per_100g=nutrition.get("fat_per_100g", 0),
                )
            )

    await session.flush()


async def seed_recipes(session: AsyncSession) -> None:
    result = await session.execute(select(Recipe).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    ing_result = await session.execute(select(Ingredient))
    ing_map = {i.name: i for i in ing_result.scalars().all()}

    tag_result = await session.execute(select(Tag))
    tag_map = {t.name: t for t in tag_result.scalars().all()}

    for recipe_data in RECIPES.values():
        nutrition = recipe_data.get("nutrition", {})
        recipe = Recipe(
            title=recipe_data["name"],
            description=f"A {recipe_data.get('cuisine', 'delicious')} recipe.",
            instructions=recipe_data["instructions"],
            servings=recipe_data.get("servings", 1),
            prep_time_minutes=recipe_data.get("prep_time_minutes", 0),
            cook_time_minutes=recipe_data.get("cook_time_minutes", 0),
            difficulty="medium",
            cuisine=recipe_data.get("cuisine", "unknown"),
        )
        session.add(recipe)
        await session.flush()

        for ing_data in recipe_data.get("ingredients", []):
            name = normalize_ingredient_name(
                ing_data["name"].lower().strip()
            )
            ing = ing_map.get(name)
            if ing:
                session.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ing.id,
                        quantity=float(ing_data["quantity"]),
                        unit=ing_data["unit"],
                        optional=False,
                    )
                )

        if nutrition:
            session.add(
                RecipeNutrition(
                    recipe_id=recipe.id,
                    calories=float(nutrition.get("calories", 0)),
                    protein=float(nutrition.get("protein", 0)),
                    carbohydrates=float(
                        nutrition.get("carbohydrates", 0)
                    ),
                    fat=float(nutrition.get("fat", 0)),
                )
            )

        cuisine_tag = recipe_data.get("cuisine", "").lower()
        if cuisine_tag and cuisine_tag not in ("healthy", "unknown"):
            if cuisine_tag not in tag_map:
                tag = Tag(name=cuisine_tag)
                session.add(tag)
                await session.flush()
                tag_map[cuisine_tag] = tag
            session.add(
                RecipeTag(
                    recipe_id=recipe.id, tag_id=tag_map[cuisine_tag].id
                )
            )

    await session.flush()


async def seed_database(session: AsyncSession) -> None:
    await seed_ingredients(session)
    await seed_recipes(session)
