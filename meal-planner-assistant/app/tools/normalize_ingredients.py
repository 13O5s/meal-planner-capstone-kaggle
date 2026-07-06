import re

from app.services.helper import optional_session
from app.services.ingredient_service import IngredientService

UNIT_ALIASES = {
    "grams": "g",
    "gram": "g",
    "gr": "g",
    "g": "g",
    "kilograms": "kg",
    "kilogram": "kg",
    "kg": "kg",
    "milliliters": "ml",
    "millilitre": "ml",
    "ml": "ml",
    "liters": "L",
    "liter": "L",
    "litre": "L",
    "l": "L",
    "tablespoons": "tbsp",
    "tablespoon": "tbsp",
    "tbsp": "tbsp",
    "teaspoons": "tsp",
    "teaspoon": "tsp",
    "tsp": "tsp",
    "cups": "cup",
    "cup": "cup",
    "pieces": "piece",
    "piece": "piece",
    "pc": "piece",
    "whole": "piece",
    "medium": "piece",
    "large": "piece",
    "cloves": "cloves",
    "clove": "cloves",
    "slices": "slice",
    "slice": "slice",
    "bottles": "bottle",
    "bottle": "bottle",
    "cans": "can",
    "can": "can",
    "packages": "package",
    "package": "package",
    "handful": "handful",
    "handfuls": "handful",
    "pinch": "pinch",
    "pinches": "pinch",
}


async def normalize_ingredients(ingredients_text: str) -> list[dict]:
    items = re.split(r"[,;\n]+", ingredients_text)
    results = []

    for item in items:
        item = item.strip()
        if not item:
            continue

        parsed = _parse_single_ingredient(item)
        if parsed:
            results.append(parsed)

    async with optional_session() as session:
        service = IngredientService(session)
        resolved = []
        for r in results:
            canonical = await service.resolve_name(r["name"])
            r["name"] = canonical
            resolved.append(r)

    return resolved


def _parse_single_ingredient(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None

    from app.data.stores import normalize_ingredient_name

    pattern = re.compile(
        r"^(?P<quantity>[\d/.]+(?:\s+[\d/.]+)?)\s*(?P<unit>\w+)?\s+(?P<name>.+)$",
        re.IGNORECASE,
    )
    half_pattern = re.compile(
        r"^(half|a\s+half|quarter|one\s+half)\s+(?P<name>.+)$",
        re.IGNORECASE,
    )
    text_only = re.compile(r"^[a-zA-Z\s]+$")

    m = pattern.match(text)
    if m:
        raw_qty = m.group("quantity")
        raw_unit = m.group("unit")
        raw_name = m.group("name").strip().lower()

        qty = _parse_fraction(raw_qty)
        unit = _resolve_unit(raw_unit) if raw_unit else "piece"
        name = normalize_ingredient_name(raw_name)

        return {
            "name": name,
            "quantity": qty,
            "unit": unit,
            "original_text": text,
        }

    m = half_pattern.match(text)
    if m:
        raw_name = m.group("name").strip().lower()

        qty = 0.5
        unit = "piece"
        name = normalize_ingredient_name(raw_name)

        return {
            "name": name,
            "quantity": qty,
            "unit": unit,
            "original_text": text,
        }

    if text_only.match(text):
        name = normalize_ingredient_name(text)
        return {
            "name": name,
            "quantity": 1,
            "unit": "piece",
            "original_text": text,
        }

    return None


def _parse_fraction(raw: str) -> float:
    try:
        if "/" in raw:
            parts = raw.split("/")
            if len(parts) == 2:
                if " " in parts[0]:
                    whole_str, frac_str = parts[0].split(" ", 1)
                    return float(whole_str) + float(frac_str) / float(parts[1])
                return float(parts[0]) / float(parts[1])
            if len(parts) == 3:
                whole = float(parts[0])
                num = float(parts[1])
                den = float(parts[2])
                return whole + num / den
        return float(raw)
    except (ValueError, ZeroDivisionError):
        return 1.0


def _resolve_unit(raw: str) -> str:
    return UNIT_ALIASES.get(raw.lower().rstrip(".").strip(), raw.lower())
