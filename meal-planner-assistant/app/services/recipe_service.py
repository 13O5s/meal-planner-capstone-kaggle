from sqlalchemy.ext.asyncio import AsyncSession

from app.data.stores import RECIPES
from app.database.models.recipe import Recipe
from app.database.repositories import RecipeRepository


class RecipeService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._repo = RecipeRepository(session) if session else None

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if self._repo:
            results = await self._repo.search_by_title(query, limit)
            return [_recipe_to_dict(r) for r in results]
        query_lower = query.lower()
        return [
            v
            for v in RECIPES.values()
            if query_lower in v["name"].lower()
        ][:limit]

    async def get_all(self) -> list[dict]:
        if self._repo:
            results = await self._repo.find(active=True)
            return [_recipe_to_dict(r) for r in results]
        return list(RECIPES.values())

    async def get_by_name(self, name: str) -> dict | None:
        if self._repo:
            recipe = await self._repo.find_by_title(name)
            return _recipe_to_dict(recipe) if recipe else None
        for _key, value in RECIPES.items():
            if value["name"].lower() == name.lower():
                return value
        return None

    async def get_by_tag(self, tag: str) -> list[dict]:
        if self._repo:
            results = await self._repo.get_by_tag(tag)
            return [_recipe_to_dict(r) for r in results]
        return list(RECIPES.values())

    async def get_by_cuisine(self, cuisine: str) -> list[dict]:
        if self._repo:
            results = await self._repo.get_by_cuisine(cuisine)
            return [_recipe_to_dict(r) for r in results]
        return [
            v for v in RECIPES.values() if v.get("cuisine", "").lower() == cuisine.lower()
        ]


def _recipe_to_dict(recipe: Recipe) -> dict:
    ingredients = []
    for ri in recipe.ingredients:
        ingredients.append({
            "name": ri.ingredient.name if ri.ingredient else ri.ingredient_name,
            "quantity": float(ri.quantity),
            "unit": ri.unit,
        })

    nutrition = {}
    if recipe.nutrition:
        n = recipe.nutrition[0] if isinstance(recipe.nutrition, list) else recipe.nutrition
        nutrition = {
            "calories": float(n.calories),
            "protein": float(n.protein),
            "carbohydrates": float(n.carbohydrates),
            "fat": float(n.fat),
        }

    return {
        "name": recipe.title,
        "ingredients": ingredients,
        "instructions": recipe.instructions or "",
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "cuisine": recipe.cuisine or "",
        "nutrition": nutrition,
    }
