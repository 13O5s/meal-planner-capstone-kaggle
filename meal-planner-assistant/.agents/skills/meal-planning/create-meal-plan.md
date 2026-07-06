# create-meal-plan

## Purpose
Generate a personalized daily or weekly meal plan by loading the user profile, analyzing nutrition goals and available inventory, recommending recipes, and validating against caloric and macronutrient targets.

## When to Use
- User requests a meal plan after profile and inventory are collected
- A new plan needs to be regenerated with different recipes or goals
- Weekly meal prep planning at the start of the week

## Prerequisites
- `user_profile` exists in session state (with `goal`, `meals_per_day`, `daily_calorie_target`)
- `available_ingredients` exists in session state (from Inventory Agent)
- `selected_recipes` exists in session state (from Recipe Agent)
- `rules/domain.md` has been reviewed for the session state contract

## Inputs
- `user_profile` dict from session state — goal, meals_per_day, calorie_target, dietary_preferences
- `selected_recipes` list from session state — recipes with ingredients and per-recipe nutrition
- Plan duration: `daily` or `weekly`

## Expected Outputs
- `session_state["meal_plan"]` — list of day dicts, each with `day`, `meals`, `total_nutrition`
- Nutrition report per day (calories, protein, carbs, fat)
- Validation result (pass/fail against daily targets with 10% tolerance)

## Step-by-Step Workflow

1. **Load user profile**: Read `session_state["user_profile"]`. Extract `goal`, `meals_per_day`, `daily_calorie_target`, and any dietary constraints.

2. **Load selected recipes**: Read `session_state["selected_recipes"]`. Each recipe should already have nutrition data from the Recipe Agent step.

3. **Distribute meals**: Based on `meals_per_day`, assign recipes to meal slots (breakfast, lunch, dinner, snacks). Distribute the daily calorie target proportionally (e.g., 25% breakfast, 35% lunch, 30% dinner, 10% snacks).

4. **Build plan**: For each day, create a list of assigned recipes. For weekly plans, rotate recipes across days to avoid repetition while respecting ingredient availability.

5. **Calculate daily nutrition**: For each day, sum the nutrition of all assigned recipes. Use `calculate_recipe_nutrition()` from `app/tools/calculate_nutrition.py`.

6. **Validate plan**: Call `validate_meal_plan()` from `app/tools/meal_plan_validator.py` with the daily calorie target and optional macro targets (protein, carbs, fat). Validation uses a 10% tolerance.

7. **Adjust if needed**: If validation fails, adjust portion sizes (multiply/divided) or swap recipes and re-validate. Repeat up to 3 attempts before accepting best effort.

8. **Store result**: Write the validated meal plan to `session_state["meal_plan"]`.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agents/meal_plan.py` — agent instruction and workflow |
| Modify | `app/tools/meal_plan_validator.py` — validation thresholds if needed |

## Validation Checklist
- [ ] Meal plan covers all `meals_per_day` slots for each day
- [ ] Daily total nutrition calculated and attached to each day
- [ ] `validate_meal_plan()` returns `valid=True` or adjustments were made
- [ ] Result stored in `session_state["meal_plan"]` with correct schema
- [ ] Weekly plans have variety (no repeated recipes back-to-back unless intentional)
- [ ] Goal type respected (high_protein prioritizes protein, budget minimizes cost, etc.)

## Common Mistakes
- Not distributing calories proportionally across meals (e.g., giving 50% to dinner)
- Ignoring the user's `goal` when assigning recipes to days
- Not validating against `daily_calorie_target` — always call `validate_meal_plan()`
- Creating boring weekly plans (same 3 recipes repeated 7 days)
- Forgetting to handle `meals_per_day` other than 3 (some users want 4-5 smaller meals)
- Using wrong unit multipliers in nutrition calculation (g vs kg, ml vs L)

## Related Rules
- `rules/domain.md` — session state contract for meal_plan, goal types, data stores
- `rules/architecture.md` — tool invocation patterns, session state conventions

## Example Usage

```python
# Input: user_profile with goal="weight_loss", meals_per_day=4,
#        daily_calorie_target=1800,
#        selected_recipes = [grilled_chicken_salad, protein_omelette, ...]

# Session state after execution:
session_state["meal_plan"] = [
    {
        "day": "Monday",
        "meals": [
            {"name": "Protein Omelette", "meal_slot": "breakfast"},
            {"name": "Grilled Chicken Salad", "meal_slot": "lunch"},
            ...
        ],
        "total_nutrition": {"calories": 1750, "protein": 120, ...}
    },
    ...
]
```
