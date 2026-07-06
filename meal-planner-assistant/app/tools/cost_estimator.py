from app.services.helper import optional_session
from app.services.ingredient_service import IngredientService


async def estimate_grocery_cost(ingredients: list[dict]) -> dict:
    async with optional_session() as session:
        service = IngredientService(session)
        total = 0.0
        itemized = []
        unknown = []

        for ing in ingredients:
            name = ing.get("name", "").lower().strip()
            qty = float(ing.get("quantity", 0))
            unit = ing.get("unit", "").lower()

            price_info = await service.get_price(name)
            if not price_info:
                unknown.append({"name": name, "reason": "No price data available"})
                continue

            base_price = price_info["price_per_unit"]
            base_unit = price_info["unit"]

            cost = _calculate_cost(qty, unit, base_price, base_unit)
            total += cost
            itemized.append(
                {
                    "name": name,
                    "quantity": qty,
                    "unit": unit,
                    "cost": round(cost, 2),
                    "category": price_info.get("category", "unknown"),
                }
            )

        return {
            "total_cost": round(total, 2),
            "itemized_costs": itemized,
            "unknown_ingredients": unknown,
            "currency": "USD",
        }


def _calculate_cost(
    qty: float, qty_unit: str, base_price: float, base_unit: str
) -> float:
    if base_unit in ("kg", "L") and qty_unit in ("g", "ml"):
        return base_price * (qty / 1000)
    if base_unit in ("kg", "L") and qty_unit in ("kg", "L"):
        return base_price * qty
    if qty_unit == base_unit or (qty_unit == "piece" and base_unit == "piece"):
        return base_price * qty
    if qty_unit == "piece" and base_unit == "kg":
        return base_price * (qty * 0.2)
    return base_price * qty
