"""
validate_domain.py — Domain model integrity checks for meal-planner-assistant.

Validates:
  Meal Plans:
    1. Calorie limits
    2. Macro limits
    3. Allergy safety
    4. Dietary restrictions
    5. Duplicate meals
    6. Meal diversity
  Shopping Lists:
    7. Duplicate ingredients
    8. Ingredient reuse
    9. Owned ingredient removal
   10. Cost estimation
  Recipes:
   11. Normalized ingredients
   12. Valid identifiers

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = APP_DIR / "data"
MODELS_DIR = APP_DIR / "models"
TOOLS_DIR = APP_DIR / "tools"
AGENTS_DIR = APP_DIR / "agents"


@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


RECIPE_SCHEMA_FIELDS = {
    "name",
    "ingredients",
    "calories",
    "protein",
    "carbs",
    "fat",
    "dietary",
    "allergens",
}

VALID_DIETARY_TAGS = {
    "vegetarian",
    "vegan",
    "gluten_free",
    "dairy_free",
    "nut_free",
    "high_protein",
    "low_carb",
    "keto",
    "paleo",
    "mediterranean",
    "none",
}

VALID_GOAL_TYPES = {"healthy", "budget", "high_protein", "weight_loss"}

MAX_CALORIES = 3500
MIN_CALORIES = 800
MAX_PROTEIN_G = 250
MAX_CARBS_G = 500
MAX_FAT_G = 150


def _parse_ast(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None


def _get_stores_module() -> dict[str, Any] | None:
    stores_path = DATA_DIR / "stores.py"
    if not stores_path.exists():
        return None
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("stores", stores_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return {
                "RECIPES": getattr(mod, "RECIPES", {}),
                "PRICE_DB": getattr(mod, "PRICE_DB", {}),
                "NUTRITION_DB": getattr(mod, "NUTRITION_DB", {}),
                "normalize_ingredient_name": getattr(
                    mod, "normalize_ingredient_name", None
                ),
            }
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# 1. Calorie limits
# ---------------------------------------------------------------------------


def check_calorie_limits() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        findings.append(
            Finding(
                field="calorie_limits",
                severity="warning",
                message="Cannot check calorie limits — stores module not found or not importable",
            )
        )
        return findings

    recipes = stores.get("RECIPES", {})
    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            calories = recipe.get("calories", 0)
            if isinstance(calories, (int, float)):
                if calories > MAX_CALORIES:
                    findings.append(
                        Finding(
                            field="calorie_limits",
                            severity="warning",
                            message=f"Recipe '{recipe_id}' has {calories} cal exceeds max {MAX_CALORIES}",
                            file=str(DATA_DIR / "stores.py"),
                        )
                    )
                elif calories < MIN_CALORIES and calories > 0:
                    findings.append(
                        Finding(
                            field="calorie_limits",
                            severity="warning",
                            message=f"Recipe '{recipe_id}' has {calories} cal below typical minimum {MIN_CALORIES}",
                            file=str(DATA_DIR / "stores.py"),
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# 2. Macro limits
# ---------------------------------------------------------------------------


def check_macro_limits() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            protein = recipe.get("protein", 0)
            carbs = recipe.get("carbs", 0)
            fat = recipe.get("fat", 0)
            if isinstance(protein, (int, float)) and protein > MAX_PROTEIN_G:
                findings.append(
                    Finding(
                        field="macro_limits",
                        severity="warning",
                        message=f"Recipe '{recipe_id}' protein {protein}g exceeds max {MAX_PROTEIN_G}g",
                        file=str(DATA_DIR / "stores.py"),
                    )
                )
            if isinstance(carbs, (int, float)) and carbs > MAX_CARBS_G:
                findings.append(
                    Finding(
                        field="macro_limits",
                        severity="warning",
                        message=f"Recipe '{recipe_id}' carbs {carbs}g exceeds max {MAX_CARBS_G}g",
                        file=str(DATA_DIR / "stores.py"),
                    )
                )
            if isinstance(fat, (int, float)) and fat > MAX_FAT_G:
                findings.append(
                    Finding(
                        field="macro_limits",
                        severity="warning",
                        message=f"Recipe '{recipe_id}' fat {fat}g exceeds max {MAX_FAT_G}g",
                        file=str(DATA_DIR / "stores.py"),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 3. Allergy safety
# ---------------------------------------------------------------------------


def check_allergy_safety() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            allergens = recipe.get("allergens", [])
            if not isinstance(allergens, list):
                continue
            known_allergens = {
                "milk",
                "eggs",
                "fish",
                "shellfish",
                "tree nuts",
                "peanuts",
                "wheat",
                "soy",
                "sesame",
                "sulfites",
                "lupin",
            }
            unknown = [a for a in allergens if a.lower() not in known_allergens]
            if unknown:
                findings.append(
                    Finding(
                        field="allergy_safety",
                        severity="warning",
                        message=f"Recipe '{recipe_id}' contains unknown allergen tags: {unknown}",
                        file=str(DATA_DIR / "stores.py"),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 4. Dietary restrictions
# ---------------------------------------------------------------------------


def check_dietary_restrictions() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            dietary = recipe.get("dietary", [])
            if isinstance(dietary, list):
                for tag in dietary:
                    if tag not in VALID_DIETARY_TAGS:
                        findings.append(
                            Finding(
                                field="dietary_restrictions",
                                severity="warning",
                                message=f"Recipe '{recipe_id}' has invalid dietary tag '{tag}' — valid tags: {sorted(VALID_DIETARY_TAGS)}",
                                file=str(DATA_DIR / "stores.py"),
                            )
                        )

    return findings


# ---------------------------------------------------------------------------
# 5. Duplicate meals
# ---------------------------------------------------------------------------


def check_duplicate_meals() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    seen_names: set[str] = set()
    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            name = recipe.get("name", recipe_id)
            name_lower = name.lower().strip()
            if name_lower in seen_names:
                findings.append(
                    Finding(
                        field="duplicate_meals",
                        severity="error",
                        message=f"Duplicate recipe name '{name}' (id: {recipe_id})",
                        file=str(DATA_DIR / "stores.py"),
                    )
                )
            seen_names.add(name_lower)

    return findings


# ---------------------------------------------------------------------------
# 6. Meal diversity
# ---------------------------------------------------------------------------


def check_meal_diversity() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    dietary_tags_seen: set[str] = set()

    for recipe in recipes.values():
        if isinstance(recipe, dict):
            dietary = recipe.get("dietary", [])
            if isinstance(dietary, list):
                dietary_tags_seen.update(dietary)

    if len(recipes) >= 3 and len(dietary_tags_seen) < 2:
        findings.append(
            Finding(
                field="meal_diversity",
                severity="info",
                message=f"Only {len(dietary_tags_seen)} dietary tag(s) across {len(recipes)} recipes — consider adding variety",
                file=str(DATA_DIR / "stores.py"),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# 7. Duplicate ingredients
# ---------------------------------------------------------------------------


def check_duplicate_ingredients() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    price_db = stores.get("PRICE_DB", {})
    seen: set[str] = set()
    for ingredient in price_db:
        key = ingredient.lower().strip()
        if key in seen:
            findings.append(
                Finding(
                    field="duplicate_ingredients",
                    severity="error",
                    message=f"Duplicate ingredient entry in PRICE_DB: '{ingredient}'",
                    file=str(DATA_DIR / "stores.py"),
                )
            )
        seen.add(key)

    return findings


# ---------------------------------------------------------------------------
# 8. Ingredient reuse
# ---------------------------------------------------------------------------


def check_ingredient_reuse() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    ingredient_recipe_map: dict[str, list[str]] = {}

    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            ingredients = recipe.get("ingredients", [])
            if isinstance(ingredients, list):
                for ing in ingredients:
                    if isinstance(ing, str):
                        key = ing.lower().strip()
                        ingredient_recipe_map.setdefault(key, []).append(recipe_id)

    single_use = [
        (ing, recipes_list)
        for ing, recipes_list in ingredient_recipe_map.items()
        if len(recipes_list) == 1
    ]
    if (
        len(single_use) > len(ingredient_recipe_map) * 0.8
        and len(ingredient_recipe_map) > 5
    ):
        findings.append(
            Finding(
                field="ingredient_reuse",
                severity="info",
                message=f"{len(single_use)} of {len(ingredient_recipe_map)} ingredients appear in only one recipe — low cross-recipe reuse",
                file=str(DATA_DIR / "stores.py"),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# 9. Owned ingredient removal
# ---------------------------------------------------------------------------


def check_owned_ingredient_removal() -> list[Finding]:
    findings: list[Finding] = []
    inventory_path = AGENTS_DIR / "inventory.py"
    if not inventory_path.exists():
        return findings

    text = inventory_path.read_text(encoding="utf-8")
    if (
        "available_ingredients" in text
        and "remove" not in text.lower()
        and "filter" not in text.lower()
    ):
        findings.append(
            Finding(
                field="owned_ingredient_removal",
                severity="warning",
                message="Inventory agent doesn't appear to filter available ingredients — should remove owned items from shopping list",
                file=str(inventory_path),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# 10. Cost estimation
# ---------------------------------------------------------------------------


def check_cost_estimation() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    price_db = stores.get("PRICE_DB", {})
    for ingredient, price in price_db.items():
        if isinstance(price, (int, float)) and price < 0:
            findings.append(
                Finding(
                    field="cost_estimation",
                    severity="error",
                    message=f"Negative price for ingredient '{ingredient}': {price}",
                    file=str(DATA_DIR / "stores.py"),
                )
            )

    cost_estimator_path = TOOLS_DIR / "cost_estimator.py"
    if cost_estimator_path.exists():
        text = cost_estimator_path.read_text(encoding="utf-8")
        if "PRICE_DB" not in text and "price" not in text.lower():
            findings.append(
                Finding(
                    field="cost_estimation",
                    severity="warning",
                    message="Cost estimator tool does not reference PRICE_DB — may not estimate costs accurately",
                    file=str(cost_estimator_path),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 11. Normalized ingredients
# ---------------------------------------------------------------------------


def check_normalized_ingredients() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    normalize_fn = stores.get("normalize_ingredient_name", None)

    if normalize_fn is None:
        findings.append(
            Finding(
                field="normalized_ingredients",
                severity="warning",
                message="normalize_ingredient_name function not found — ingredient normalization may be incomplete",
                file=str(DATA_DIR / "stores.py"),
            )
        )
        return findings

    for recipe_id, recipe in recipes.items():
        if isinstance(recipe, dict):
            ingredients = recipe.get("ingredients", [])
            if isinstance(ingredients, list):
                for ing in ingredients:
                    if isinstance(ing, str) and ing.strip():
                        try:
                            normalized = normalize_fn(ing)
                            if normalized is None or normalized == ing:
                                pass
                        except Exception:
                            findings.append(
                                Finding(
                                    field="normalized_ingredients",
                                    severity="warning",
                                    message=f"normalize_ingredient_name failed for '{ing}' in recipe '{recipe_id}'",
                                    file=str(DATA_DIR / "stores.py"),
                                )
                            )

    return findings


# ---------------------------------------------------------------------------
# 12. Valid identifiers
# ---------------------------------------------------------------------------


def check_valid_identifiers() -> list[Finding]:
    findings: list[Finding] = []
    stores = _get_stores_module()
    if stores is None:
        return findings

    recipes = stores.get("RECIPES", {})
    for recipe_id in recipes:
        if not isinstance(recipe_id, str) or not recipe_id.strip():
            findings.append(
                Finding(
                    field="valid_identifiers",
                    severity="error",
                    message=f"Empty or invalid recipe identifier: '{recipe_id}'",
                    file=str(DATA_DIR / "stores.py"),
                )
            )
        elif not recipe_id.replace("_", "").replace("-", "").isalnum():
            findings.append(
                Finding(
                    field="valid_identifiers",
                    severity="warning",
                    message=f"Recipe identifier '{recipe_id}' contains special characters — prefer snake_case",
                    file=str(DATA_DIR / "stores.py"),
                )
            )

    price_db = stores.get("PRICE_DB", {})
    for ingredient in price_db:
        if not isinstance(ingredient, str) or not ingredient.strip():
            findings.append(
                Finding(
                    field="valid_identifiers",
                    severity="error",
                    message=f"Empty or invalid ingredient key in PRICE_DB: '{ingredient}'",
                    file=str(DATA_DIR / "stores.py"),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, str, Any]] = [
    ("Calorie limits", "warning", check_calorie_limits),
    ("Macro limits", "warning", check_macro_limits),
    ("Allergy safety", "warning", check_allergy_safety),
    ("Dietary restrictions", "warning", check_dietary_restrictions),
    ("Duplicate meals", "error", check_duplicate_meals),
    ("Meal diversity", "info", check_meal_diversity),
    ("Duplicate ingredients", "error", check_duplicate_ingredients),
    ("Ingredient reuse", "info", check_ingredient_reuse),
    ("Owned ingredient removal", "warning", check_owned_ingredient_removal),
    ("Cost estimation", "warning", check_cost_estimation),
    ("Normalized ingredients", "warning", check_normalized_ingredients),
    ("Valid identifiers", "error", check_valid_identifiers),
]


def main() -> int:
    all_findings: list[Finding] = []
    for check_name, _severity, check_func in CHECKS:
        try:
            findings = check_func()
            if findings:
                for f in findings:
                    tag = (
                        "FAIL"
                        if f.severity == "error"
                        else "WARN"
                        if f.severity == "warning"
                        else "INFO"
                    )
                    loc = f" [{f.file}" + (f":{f.line}" if f.line else "") + "]"
                    print(f"  [{tag}] {f.field}: {f.message}{loc}")
                all_findings.extend(findings)
        except Exception as e:
            print(f"  [ERROR] {check_name} crashed: {e}", file=sys.stderr)
            all_findings.append(
                Finding(
                    field=check_name, severity="error", message=f"Checker crashed: {e}"
                )
            )

    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warning"]

    print(
        f"\nDomain validation: {len(errors)} errors, {len(warnings)} warnings, {len(all_findings)} total"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
