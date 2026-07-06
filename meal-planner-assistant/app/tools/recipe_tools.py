from app.services.helper import optional_session
from app.services.nutrition_service import NutritionService
from app.services.recipe_service import RecipeService


async def search_recipes(
    query: str = "",
    cuisine: str = "",
    max_results: int = 10,
) -> list[dict]:
    async with optional_session() as session:
        recipe_service = RecipeService(session)
        nutrition_service = NutritionService(session)

        if cuisine:
            results = await recipe_service.get_by_cuisine(cuisine)
        elif query:
            results = await recipe_service.search(query, max_results)
        else:
            results = await recipe_service.get_all()

        recipes_with_nutrition = []
        for recipe in results[:max_results]:
            ingredients = recipe.get("ingredients", [])
            nutrition_data = recipe.get("nutrition")
            if not nutrition_data:
                nutrition_data = await nutrition_service.calculate(ingredients)
            recipes_with_nutrition.append({
                **recipe,
                "nutrition": nutrition_data,
            })

        return recipes_with_nutrition
