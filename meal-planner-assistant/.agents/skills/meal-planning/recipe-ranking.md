# recipe-ranking

## Purpose
Rank recipes from the in-memory database by suitability for the user, considering ingredient availability, nutrition alignment, preferences, cooking time, budget, and meal diversity.

## When to Use
- After inventory is collected, to recommend what the user can cook
- User asks "what can I make with what I have?"
- Regenerating recommendations after the user rejects initial suggestions

## Prerequisites
- `user_profile` exists in session state (with preferences, allergies, goal, budget)
- `available_ingredients` exists in session state
- `app/data/stores.py` `RECIPES` dict is populated with seed recipes

## Inputs
- `user_profile` dict — favorite_foods, disliked_foods, allergies, dietary_preferences, goal, budget
- `available_ingredients` list — what the user has at home
- `RECIPES` from `app/data/stores.py` — the seed recipe database

## Expected Outputs
- Top 3-5 ranked recipe recommendations with ranking rationale
- `session_state["selected_recipes"]` — user's confirmed selection
- Per-recipe nutrition data (from `calculate_recipe_nutrition()`)

## Step-by-Step Workflow

1. **Load inputs**: Read `user_profile` and `available_ingredients` from session state.

2. **Exclude ineligible recipes**: Remove any recipe that contains ingredients from the user's `disliked_foods` or `allergies` lists.

3. **Score each recipe** on five weighted criteria (suggested weights: 35% availability, 25% preference, 20% nutrition, 10% time, 10% diversity):

   - **Ingredient availability (35%)**: Percentage of recipe ingredients the user already has. Prefer recipes that need fewer purchases.
   - **User preference (25%)**: Boost score for recipes matching `favorite_foods` or `dietary_preferences` (e.g., "vegetarian", "high_protein"). Neutral for others.
   - **Nutrition alignment (20%)**: How well the recipe's calories and macros fit the user's goal (`weight_loss` → lower calorie, `high_protein` → higher protein).
   - **Cooking time (10%)**: Prefer quick recipes on weekdays. Adjust based on implied schedule from profile.
   - **Meal diversity (10%)**: If multiple recipes are from the same cuisine, penalize repeats to encourage variety over the week.

4. **Calculate nutrition**: For each top candidate, call `calculate_recipe_nutrition()` to get per-recipe nutritional data.

5. **Present top recommendations**: Show the top 3-5 recipes with:
   - Recipe name
   - Why it was chosen for this user (ingredient match, preference match, goal alignment)
   - Key nutrition stats (calories, protein)
   - Estimated cost

6. **Store user selection**: Save the user's confirmed selection in `session_state["selected_recipes"]`.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agents/recipe.py` — agent instruction and ranking logic |
| Modify | `app/data/stores.py` — RECIPES entries (if adding new recipes) |

## Validation Checklist
- [ ] Disliked foods and allergens are excluded from candidates
- [ ] Ranking weights are balanced — no single factor dominates unfairly
- [ ] Top recommendations include user-specific reasoning
- [ ] Per-recipe nutrition is calculated for all candidates
- [ ] No more than 5 recommendations shown (avoid choice overload)
- [ ] Selected recipes stored in `session_state["selected_recipes"]`

## Common Mistakes
- Not excluding recipes containing allergens
- Ranking solely by ingredient availability (ignoring preferences and goals)
- Recommending 8+ options — causes decision paralysis, limit to 3-5
- Not explaining why a recipe was chosen — user needs context to decide
- Recommending recipes from the same cuisine repeatedly (low diversity)
- Forgetting to calculate per-recipe nutrition before presenting

## Related Rules
- `rules/domain.md` — RECIPES data format, goal types, session state contract
- `rules/architecture.md` — tool invocation for nutrition calculation

## Example Usage

```python
# Input: user has chicken, eggs, broccoli
#        user_profile: goal="high_protein", dislikes seafood
#        available_ingredients: chicken breast, eggs, broccoli

# Ranking (simplified):
# 1. Protein Omelette      — 80% avail, high protein, 10min → score 92
# 2. Grilled Chicken Salad — 60% avail, high protein, 27min → score 78
# 3. Vegetable Stir Fry    — 40% avail, low protein, 20min  → score 55
# [excluded: Pasta Bolognese — no ingredient match, 0% avail]

# Output: top 3 presented to user with reasons
```
