# optimize-shopping-list

## Purpose
Generate a cost-optimized grocery list that merges duplicate ingredients across recipes, removes items already available, minimizes food waste, and estimates total cost against the user's budget.

## When to Use
- After a meal plan is finalized and selected recipes are known
- User wants to know what to buy and how much it will cost
- Budget checking is needed before committing to a meal plan

## Prerequisites
- `selected_recipes` exists in session state (recipe list with ingredients)
- `available_ingredients` exists in session state (what the user already has)
- `user_profile` exists in session state (includes `budget`)

## Inputs
- `selected_recipes` list from session state — recipes, each with `ingredients` list
- `available_ingredients` list from session state — ingredients user has with quantities
- `user_profile` dict with `budget` field (float, USD)

## Expected Outputs
- `session_state["shopping_list"]` — list of items with ingredient_name, total_quantity, unit, estimated_cost, category
- Total cost estimate
- Budget compliance flag (under/over budget with suggested swaps if over)
- Items grouped by category (meat, dairy, vegetables, pantry, fruit)

## Step-by-Step Workflow

1. **Load inputs**: Read `selected_recipes`, `available_ingredients`, and `user_profile` from session state.

2. **Merge ingredients across recipes**: For each recipe in `selected_recipes`, collect all ingredients. Group by `(name, unit)` and sum quantities for duplicates (e.g., "chicken breast" appears in 3 recipes → total quantity).

3. **Subtract available stock**: For each merged ingredient, subtract the quantity the user already has (from `available_ingredients`). If the user has more than needed, exclude the ingredient entirely. If partially stocked, include only the deficit.

4. **Minimize waste**: When calculating quantities, round up to the nearest standard package size where applicable (e.g., eggs by dozen, milk by liter). Note: this is an estimate — the shopping agent can suggest rounding strategies.

5. **Estimate costs**: For each needed ingredient, look up the unit price from `PRICE_DB` in `app/data/stores.py`. Calculate `quantity_needed * price_per_unit`. Flag ingredients not in `PRICE_DB` as unknown cost.

6. **Check budget**: Sum all estimated costs. Compare against `user_profile["budget"]`. If over budget, identify the most expensive items and suggest cheaper alternatives or recipe swaps.

7. **Categorize and store**: Group items by `category` (from `PRICE_DB`). Store the final list in `session_state["shopping_list"]` as `ShoppingListItem` dicts.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agents/shopping.py` — agent instruction |
| Modify | `app/tools/shopping_list.py` — merge/deduplicate logic |
| Modify | `app/tools/cost_estimator.py` — cost calculation |
| Modify | `app/data/stores.py` — PRICE_DB entries (if new ingredients needed) |

## Validation Checklist
- [ ] Duplicate ingredients across recipes are merged, not duplicated
- [ ] Available ingredients are subtracted (including partial quantities)
- [ ] Waste is minimized (quantities rounded up to practical amounts)
- [ ] Total cost is estimated and compared against budget
- [ ] Over-budget scenarios include alternative suggestions
- [ ] Items are grouped by category for organized presentation
- [ ] Unknown ingredients (not in PRICE_DB) are flagged
- [ ] Result stored in `session_state["shopping_list"]`

## Common Mistakes
- Not subtracting available ingredient quantities before adding to list
- Double-counting the same ingredient across different recipes
- Using inconsistent units for the same ingredient (e.g., "chicken breast" once in g, once in kg)
- Forgetting to check the user's budget before finalizing the list
- Not rounding quantities to practical purchase sizes (e.g., 0.3L of milk — suggest 1L)
- Flagging unknown ingredients as errors instead of estimates

## Related Rules
- `rules/domain.md` — session state contract, PRICE_DB, category mapping
- `rules/architecture.md` — tool invocation patterns
- `rules/coding.md` — data handling, type annotations

## Example Usage

```python
# Input:
#   selected_recipes = [grilled_chicken_salad, pasta_bolognese]
#   available_ingredients = [{name: "chicken breast", quantity: 200, unit: "g", available: true}]
#   user_profile["budget"] = 50.0

# Output session_state["shopping_list"]:
[
    {"ingredient_name": "pasta", "total_quantity": 200, "unit": "g", "estimated_cost": 0.50, "category": "pantry"},
    {"ingredient_name": "ground beef", "total_quantity": 250, "unit": "g", "estimated_cost": 2.50, "category": "meat"},
    {"ingredient_name": "tomato", "total_quantity": 1, "unit": "piece", "estimated_cost": 1.50, "category": "vegetables"},
    # ... chicken breast excluded because user already has 200g
]
# total_cost: 24.30 — under budget of 50.0 ✓
```
