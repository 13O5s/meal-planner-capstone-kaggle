# Domain Rules

## Purpose

Document the meal-planning domain model, session state contract, and data store layout so agents understand the problem domain.

## Principles

- The domain has 6 core stages: Profile → Inventory → Recipe → Meal Plan → Nutrition → Shopping
- Each stage produces a session state key consumed by downstream stages
- In-memory data stores (`app/data/stores.py`) provide seed data for recipes, prices, and nutrition

## Required Practices

### Session state contract

| Key | Written By | Read By | Format |
|---|---|---|---|
| `user_profile` | Profile Agent | Recipe, Meal Plan, Nutrition, Shopping | `dict` with age, gender, height_cm, weight_kg, activity_level, goal, dietary_preferences, allergies, budget, meals_per_day |
| `available_ingredients` | Inventory Agent | Recipe, Meal Plan, Shopping | `list[dict]` with name, quantity, unit, available=true |
| `requested_ingredients` | Inventory Agent | — | `list[dict]` with name, quantity, unit |
| `selected_recipes` | Recipe Agent | Meal Plan, Nutrition, Shopping | `list[dict]` matching RECIPES format |
| `meal_plan` | Meal Plan Agent | — | `list[dict]` with day, meals, total_nutrition |
| `nutrition_validation` | Nutrition Agent | — | `dict` with meets_calories, meets_protein, etc. |
| `shopping_list` | Shopping Agent | — | `list[dict]` with ingredient_name, quantity, unit, cost, category |

### Data stores

- `app/data/stores.py` contains: `RECIPES` (5 seed recipes), `PRICE_DB` (~22 ingredients with prices), `NUTRITION_DB` (~22 ingredients with per-100g/per-piece values), `normalize_ingredient_name()` for alias resolution
- Extend the dicts to add data. Swap in a database service when persistence is needed

### Goal types
- `healthy` — balanced macros
- `budget` — minimize cost
- `high_protein` — maximize protein
- `weight_loss` — calorie deficit

## Forbidden Practices

- Using session state keys outside the documented contract
- Storing data outside `app/data/stores.py` without explicit reason
- Adding recipe data that lacks the required schema fields

## Examples

```python
# Reading session state
profile = session_state.get("user_profile", {})
goal = profile.get("goal", "healthy")

# Writing session state
session_state["meal_plan"] = generated_plan
```
