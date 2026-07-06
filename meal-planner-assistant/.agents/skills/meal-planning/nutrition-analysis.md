# nutrition-analysis

## Purpose
Calculate nutritional content (calories, protein, carbohydrates, fat) for recipes and validate meal plans against daily macro targets, providing actionable adjustment suggestions.

## When to Use
- After recipes are selected, to verify they meet the user's nutritional goals
- After a meal plan is generated, to validate daily totals
- User asks "does this meal meet my protein target?"

## Prerequisites
- `NUTRITION_DB` in `app/data/stores.py` is populated with per-100g and per-piece values
- For recipe analysis: a list of ingredients with name, quantity, and unit
- For meal plan validation: a meal plan with per-day `total_nutrition` and user's daily targets

## Inputs
- For recipe analysis: `list[dict]` of ingredients, each with `name`, `quantity`, `unit`
- For plan validation: `list[dict]` meal plan with `day` and `total_nutrition` keys, plus `daily_calorie_target`, `daily_protein_target`, `daily_carbs_target`, `daily_fat_target`

## Expected Outputs
- `dict` with calories, protein, carbohydrates, fat for a recipe or day
- `dict` with `valid` (bool), `day_results` (per-day pass/fail), `summary` (text) for plan validation
- Adjustment suggestions if targets are not met

## Step-by-Step Workflow

1. **Calculate recipe nutrition**: Call `calculate_recipe_nutrition(ingredients)`. The function looks up each ingredient in `NUTRITION_DB`, applies the correct multiplier based on unit type (per_100g, per_piece, per_100ml), and sums the totals. Unknown ingredients are silently skipped.

2. **Validate meal plan**: Call `validate_meal_plan(meal_plan, daily_calorie_target, ...)`. The function applies a 10% tolerance to each target and returns a per-day pass/fail breakdown.

3. **Analyze shortfalls**: If validation fails, determine which macros are deficient or excessive:
   - Protein low → suggest adding high-protein ingredients (chicken, eggs, Greek yogurt)
   - Fat high → suggest reducing oil, fatty meats, or portion sizes
   - Carbs imbalanced → suggest swapping refined carbs for complex carbs
   - Calories off → suggest adjusting portion sizes across all meals

4. **Generate suggestions**: Produce concrete, actionable recommendations (not generic advice). Example: "Add 100g chicken breast to dinner (+31g protein)."

5. **Store results**: Write the validation results to `session_state["nutrition_validation"]`.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agents/nutrition.py` — agent instruction |
| Modify | `app/tools/calculate_nutrition.py` — nutrition lookup and calculation |
| Modify | `app/tools/meal_plan_validator.py` — validation against targets |
| Modify | `app/data/stores.py` — NUTRITION_DB entries (if new ingredients needed) |

## Validation Checklist
- [ ] Per-recipe nutrition calculated correctly (calories, protein, carbs, fat)
- [ ] Unit conversions correct: g/100, kg/100*1000, ml/100, L/100*1000, pieces as-is
- [ ] Unknown ingredients handled gracefully (skipped, not error)
- [ ] Meal plan validation uses 10% tolerance as configured
- [ ] Adjustment suggestions are concrete and actionable
- [ ] `session_state["nutrition_validation"]` written with pass/fail and details
- [ ] `per_piece` entries handled separately from `per_100g` entries

## Common Mistakes
- Using `g` multiplier when data is `per_100g` (must divide by 100)
- Using wrong unit multiplier: `kg` = g * 1000, then divide by 100 for per_100g
- Assuming all ingredients exist in `NUTRITION_DB` — always handle missing keys
- Suggesting vague adjustments ("eat less fat") instead of concrete ones ("replace 2tbsp olive oil with cooking spray")
- Forgetting that `per_piece` nutrition exists (eggs, banana) and treating them as per_100g
- Not updating `NUTRITION_DB` when adding new ingredients to recipes

## Related Rules
- `rules/domain.md` — NUTRITION_DB layout, session state keys, goal types
- `rules/coding.md` — data handling, type annotations

## Example Usage

```python
# Input: ingredients for Grilled Chicken Salad
ingredients = [
    {"name": "chicken breast", "quantity": 200, "unit": "g"},
    {"name": "lettuce", "quantity": 100, "unit": "g"},
    {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
]

# Output:
{"calories": 414.4, "protein": 62.0, "carbohydrates": 3.4, "fat": 17.2}

# For plan validation:
validate_meal_plan(meal_plan, daily_calorie_target=2000)
# Output: {"valid": true, "day_results": [...], "summary": "All days meet targets"}
```
