# inventory-normalization

## Purpose
Parse free-form user ingredient descriptions into structured `{name, quantity, unit}` objects, normalizing names through alias resolution and units through standard mapping, while detecting invalid or unrecognizable inputs.

## When to Use
- User provides their available ingredients in natural language (e.g., "2 eggs, 200g chicken, half onion")
- User adds new ingredients mid-conversation
- Normalizing recipe ingredients before nutrition calculation or shopping list generation

## Prerequisites
- `app/data/stores.py` has `normalize_ingredient_name()` alias mapping and `UNIT_ALIASES`
- Ingredient text is in free-form string format (comma-separated or newline-separated)

## Inputs
- `ingredients_text`: string with one or more ingredient descriptions
  - Examples: `"2 eggs"`, `"200g chicken breast"`, `"half bottle of olive oil"`, `"3 cloves garlic"`
  - Multiple items: comma-separated (`"2 eggs, 200g chicken"`) or newline-separated

## Expected Outputs
- `list[dict]` of normalized ingredients, each with `name`, `quantity` (float), `unit`, `original_text`
- Detection and flagging of unrecognized ingredients (not in alias mapping)
- Confirmation prompt for ambiguous quantities (e.g., "1 onion" — what size?)
- `session_state["available_ingredients"]` — normalized available ingredients
- `session_state["requested_ingredients"]` — normalized requested ingredients

## Step-by-Step Workflow

1. **Parse input text**: Call `normalize_ingredients(ingredients_text)` from `app/tools/normalize_ingredients.py`. The function splits on commas, semicolons, and newlines; then parses each item with regex patterns:
   - `"<quantity> <unit> <name>"` — e.g., "200g chicken breast"
   - `"half <name>"` — e.g., "half onion" → quantity 0.5
   - `"<name>"` only — e.g., "eggs" → quantity 1, unit "piece"

2. **Normalize names**: Each extracted name passes through `normalize_ingredient_name()` in `app/data/stores.py`, which resolves aliases ("chicken" → "chicken breast", "eggs" → "egg", "bell peppers" → "bell pepper").

3. **Normalize units**: Units are resolved through `UNIT_ALIASES` in `app/tools/normalize_ingredients.py` ("grams" → "g", "ml" → "ml", "pieces" → "piece").

4. **Handle fractions**: Quantities like "1/2", "2 1/2", "1/3" are parsed to float values via `_parse_fraction()`.

5. **Detect invalid ingredients**: If an ingredient name cannot be resolved through the alias mapping and doesn't match any known pattern, flag it for user clarification rather than silently dropping it.

6. **Merge duplicates**: If the user provides the same ingredient multiple times (e.g., "2 eggs, 3 eggs"), sum the quantities and keep one entry.

7. **Request confirmation**: If any quantities are ambiguous (no unit specified, or unit-less items like "1 onion"), ask the user to confirm or clarify.

8. **Store in session state**: Write the normalized available list to `session_state["available_ingredients"]` and requested list to `session_state["requested_ingredients"]`.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agents/inventory.py` — agent instruction |
| Modify | `app/tools/normalize_ingredients.py` — parsing and normalization logic |
| Modify | `app/data/stores.py` — `normalize_ingredient_name()` aliases and `UNIT_ALIASES` |

## Validation Checklist
- [ ] Free-form text parsed into structured dicts for each ingredient
- [ ] Units normalized to canonical forms (g, kg, ml, L, piece, tbsp, tsp)
- [ ] Ingredient names resolved through alias mapping
- [ ] Fractions parsed correctly (1/2, 1/3, 2 1/2, 3/4)
- [ ] Duplicate ingredients merged with summed quantities
- [ ] Invalid/unrecognized ingredients flagged, not silently dropped
- [ ] User prompted to confirm ambiguous quantities
- [ ] Results stored in both `available_ingredients` and `requested_ingredients`

## Common Mistakes
- Not handling fraction formats — "1/2" is valid but "½" (Unicode) is not
- Missing unit aliases for common terms like "gr" (g), "pc" (piece), "dozen"
- Not asking for confirmation when quantity or unit is missing
- Silently dropping unrecognized ingredients instead of flagging them
- Not merging duplicates — if user says "2 eggs, 3 eggs", result should be 5 eggs
- Ingredient name aliasing too aggressive ("chicken" → "chicken breast" when user meant "whole chicken")

## Related Rules
- `rules/domain.md` — data store layout, normalize_ingredient_name mapping, session state keys
- `rules/coding.md` — type annotations for the normalized output

## Example Usage

```python
# Input:
normalize_ingredients("2 eggs, 200g chicken breast, half onion, 3 cloves garlic")

# Output:
[
    {"name": "eggs", "quantity": 2.0, "unit": "piece", "original_text": "2 eggs"},
    {"name": "chicken breast", "quantity": 200.0, "unit": "g", "original_text": "200g chicken breast"},
    {"name": "onion", "quantity": 0.5, "unit": "piece", "original_text": "half onion"},
    {"name": "garlic", "quantity": 3.0, "unit": "cloves", "original_text": "3 cloves garlic"},
]
```
