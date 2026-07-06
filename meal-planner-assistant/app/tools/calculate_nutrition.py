from app.services.helper import optional_session
from app.services.nutrition_service import NutritionService


async def calculate_recipe_nutrition(ingredients: list[dict]) -> dict:
    async with optional_session() as session:
        service = NutritionService(session)
        return await service.calculate(ingredients)
