import time

from app.data.stores import NUTRITION_DB, PRICE_DB, normalize_ingredient_name
from app.tools.normalize_ingredients import UNIT_ALIASES

_INVENTORY_DB: dict[str, list[dict]] = {}
_KNOWN_INGREDIENTS: set[str] = set(NUTRITION_DB.keys()) | set(PRICE_DB.keys())


def save_inventory(user_id: str, ingredients: list[dict]) -> dict:
    if not user_id or not isinstance(ingredients, list):
        return {"saved": False, "error": "user_id and ingredients list are required"}
    normalized = []
    for ing in ingredients:
        raw_name = ing.get("name", "")
        raw_qty = ing.get("quantity", 0)
        raw_unit = ing.get("unit", "")
        name = normalize_ingredient_name(raw_name)
        unit = _resolve_unit(raw_unit)
        qty = float(raw_qty) if isinstance(raw_qty, (int, float)) else 0.0
        normalized.append({
            "name": name,
            "quantity": qty,
            "unit": unit,
            "available": ing.get("available", True),
        })
    _INVENTORY_DB[user_id] = normalized
    return {"saved": True, "user_id": user_id, "count": len(normalized), "timestamp": time.time()}


def get_inventory(user_id: str) -> dict:
    if not user_id:
        return {"found": False, "error": "user_id is required"}
    items = _INVENTORY_DB.get(user_id)
    if items is None:
        return {"found": False, "user_id": user_id}
    return {"found": True, "user_id": user_id, "ingredients": list(items)}


def normalize_ingredient(raw_name: str, raw_quantity: float = 1.0, raw_unit: str = "piece") -> dict:
    name = normalize_ingredient_name(raw_name)
    unit = _resolve_unit(raw_unit)
    qty = float(raw_quantity) if isinstance(raw_quantity, (int, float)) else 1.0
    known = name in _KNOWN_INGREDIENTS
    return {
        "name": name,
        "quantity": qty,
        "unit": unit,
        "known": known,
        "original_text": f"{raw_quantity} {raw_unit} {raw_name}".strip(),
    }


def _resolve_unit(raw: str) -> str:
    cleaned = raw.strip().lower().rstrip(".").strip()
    return UNIT_ALIASES.get(cleaned, cleaned)
