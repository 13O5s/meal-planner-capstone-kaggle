from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import NutritionInfo
from app.services.ingredient_service import IngredientService


class NutritionService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._ingredient_service = IngredientService(session)

    async def calculate(self, ingredients: list[dict]) -> dict:
        total = NutritionInfo(calories=0, protein=0, carbohydrates=0, fat=0)

        for ing in ingredients:
            name = ing.get("name", "").lower().strip()
            qty = float(ing.get("quantity", 0))
            unit = ing.get("unit", "").lower()

            info = await self._ingredient_service.get_nutrition(name)
            if not info:
                continue

            multiplier = _get_multiplier(info, qty, unit)
            total.calories += _lookup_value(info, "calories", multiplier)
            total.protein += _lookup_value(info, "protein", multiplier)
            total.carbohydrates += _lookup_value(info, "carbs", multiplier)
            total.fat += _lookup_value(info, "fat", multiplier)

        return total.model_dump()


def _get_multiplier(info: dict, qty: float, unit: str) -> float:
    keys = list(info.keys())
    per_key = "per_100g"
    for k in keys:
        if "_per_" in k:
            per_key = "per_" + k.split("_per_", 1)[1]
            break

    if per_key == "per_piece":
        return qty
    if per_key == "per_100ml":
        if unit in ("ml", "milliliter", "millilitre"):
            return qty / 100
        if unit in ("l", "liter", "litre"):
            return (qty * 1000) / 100
        return qty
    if unit in ("g", "gram", "grams", "gr"):
        return qty / 100
    if unit in ("kg", "kilogram", "kilograms"):
        return (qty * 1000) / 100
    if unit in ("ml", "milliliter", "millilitre"):
        return qty / 100
    if unit in ("l", "liter", "litre"):
        return (qty * 1000) / 100
    return qty / 100


def _lookup_value(info: dict, key: str, multiplier: float) -> float:
    for db_key in info:
        if key in db_key:
            return info[db_key] * multiplier
    return 0.0
