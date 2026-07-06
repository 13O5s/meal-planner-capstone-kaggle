from app.services.helper import optional_session
from app.services.shopping_service import ShoppingService


async def generate_optimized_shopping_list(
    selected_recipes: list[dict],
    available_ingredients: list[dict],
) -> list[dict]:
    async with optional_session() as session:
        service = ShoppingService(session)
        return await service.generate_shopping_list(
            selected_recipes, available_ingredients
        )
