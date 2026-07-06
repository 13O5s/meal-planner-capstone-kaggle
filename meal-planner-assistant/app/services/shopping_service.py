from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ShoppingListItem
from app.services.ingredient_service import IngredientService


class ShoppingService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._ingredient_service = IngredientService(session)

    async def generate_shopping_list(
        self,
        selected_recipes: list[dict],
        available_ingredients: list[dict],
    ) -> list[dict]:
        combined: dict[tuple[str, str], dict] = {}
        avail_map = _build_available_map(available_ingredients)

        for recipe in selected_recipes:
            for ing in recipe.get("ingredients", []):
                name = ing.get("name", "").lower().strip()
                qty = float(ing.get("quantity", 0))
                unit = ing.get("unit", "").lower()
                key = (name, unit)

                if key in combined:
                    combined[key]["total_quantity"] += qty
                else:
                    combined[key] = {
                        "name": name,
                        "total_quantity": qty,
                        "unit": unit,
                    }

        result = []
        for (name, unit), data in combined.items():
            total_qty = data["total_quantity"]

            if name in avail_map:
                avail_qty = _to_base_unit(
                    avail_map[name]["quantity"], avail_map[name]["unit"]
                )
                needed_qty = total_qty - avail_qty
                if needed_qty <= 0:
                    continue
            else:
                needed_qty = total_qty

            price_info = await self._ingredient_service.get_price(name)
            unit_price = price_info.get("price_per_unit", 0) if price_info else 0
            base_unit = price_info.get("unit", unit) if price_info else unit
            cost = round(
                unit_price * _normalize_to_base(needed_qty, unit, base_unit), 2
            )

            result.append(
                ShoppingListItem(
                    ingredient_name=name,
                    total_quantity=round(needed_qty, 2),
                    unit=unit,
                    estimated_cost=cost,
                    category=price_info.get("category", "unknown") if price_info else "unknown",
                ).model_dump()
            )

        return result


def _build_available_map(ingredients: list[dict]) -> dict[str, dict]:
    result = {}
    for ing in ingredients:
        name = ing.get("name", "").lower().strip()
        if name:
            result[name] = ing
    return result


def _to_base_unit(qty: float, unit: str) -> float:
    if unit in ("kg",):
        return qty * 1000
    if unit in ("L",):
        return qty * 1000
    return qty


def _normalize_to_base(qty: float, unit: str, base_unit: str) -> float:
    if base_unit == "piece":
        return qty
    if base_unit in ("kg", "L"):
        if unit in ("g", "ml"):
            return qty / 1000
        if unit in ("kg", "L"):
            return qty
        return qty * 0.2
    return qty
