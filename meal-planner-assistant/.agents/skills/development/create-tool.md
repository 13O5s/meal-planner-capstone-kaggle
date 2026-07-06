# create-tool

## Purpose
Create a reusable function tool with typed request/response models, business logic, unit tests, and agent registration.

## When to Use
- Adding a new capability that an agent needs to invoke during execution
- Extracting logic from an agent's instruction into a testable, reusable function
- Wrapping an external API or data store query for agent consumption

## Prerequisites
- The tool's input parameters and return shape are defined
- The data stores (`app/data/stores.py`) have been extended if new reference data is needed
- `rules/coding.md` and `rules/architecture.md` have been reviewed

## Inputs
- Tool function name (snake_case)
- Input parameters with types (`list[str]`, `dict[str, float]`, `str | None`, etc.)
- Return value shape (dict keys or Pydantic model)
- Business logic description
- Which agent(s) will use this tool

## Expected Outputs
- Request/response Pydantic models in `app/models/schemas.py` (or dedicated models file)
- Tool implementation in `app/tools/<name>.py`
- Tool registered in the consuming agent's `tools=[...]`
- `tests/unit/test_<name>.py` with coverage for known cases, edge cases, and error paths

## Step-by-Step Workflow

1. **Define request model** (optional): If the tool takes complex structured input, add a Pydantic model to `app/models/schemas.py`. For simple parameters (str, int, list of dicts), function signature types are sufficient — the LLM reads them from the docstring schema.

2. **Define response model** (optional): If the tool returns complex structured output, add a Pydantic model to `app/models/schemas.py`. The function must call `.model_dump()` before returning. Follow `rules/coding.md`.

3. **Implement business logic**: Create `app/tools/<name>.py` with a plain Python function. Include:
   - Complete docstring with `Args:` and `Returns:` sections (this becomes the LLM's tool schema)
   - Input validation (handle missing keys, invalid values gracefully)
   - Data lookup from `app/data/stores.py` if needed
   - The function must accept and return only JSON-serializable types

4. **Register the tool**: In the consuming agent's factory file (`app/agents/<agent>.py`):
   - Import the function: `from app.tools.<name> import <function>`
   - Add to `tools=[..., <function>]`

5. **Create unit tests**: Create `tests/unit/test_<name>.py` covering:
   - Known inputs with expected outputs
   - Edge cases: empty input, missing keys, boundary values
   - Error paths: unknown data lookups, invalid units
   - Mock `app.data.stores` if tests should isolate from seed data

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/models/schemas.py` — request/response models (if needed) |
| Create | `app/tools/<name>.py` — function implementation |
| Modify | `app/agents/<agent>.py` — import + register in tools list |
| Modify | `app/data/stores.py` — new reference data (if needed) |
| Create | `tests/unit/test_<name>.py` |

## Validation Checklist
- [ ] Function has a complete docstring with `Args:` and `Returns:` sections
- [ ] Type annotations use modern syntax (`list[str]`, `str | None`, `dict[str, float]`)
- [ ] Returns only JSON-serializable types (Pydantic models exported via `.model_dump()`)
- [ ] No side effects beyond reading from data stores or calling stable APIs
- [ ] Imported as function reference: `from app.tools.<name> import <func>`, not `import app.tools.<name>`
- [ ] Registered in exactly the agents that need it
- [ ] `ruff check` passes (no unused imports, proper formatting)
- [ ] `uv run pytest tests/unit/test_<name>.py` passes with >90% coverage
- [ ] LLM can infer calling convention from the docstring alone

## Common Mistakes
- Omitting docstring — the LLM cannot invoke the tool without understanding its schema
- Returning a Pydantic model object instead of `.model_dump()` dict — not JSON-serializable
- Importing the module (`import app.tools.x`) instead of the function (`from app.tools.x import f`)
- Adding business logic that belongs in an agent instruction or a service layer
- Not testing edge cases (empty ingredient list, unknown units, missing quantities)
- Using `List[str]` instead of `list[str]` — fails `ruff check`

## Related Rules
- `rules/coding.md` — type annotations, import order, line length, style
- `rules/architecture.md` — tool import conventions, session state patterns
- `rules/testing.md` — unit test organization, pytest conventions
- `rules/domain.md` — data store layout for reference lookups

## Example Usage

```python
# Input: tool to calculate recipe nutrition
#   name: calculate_recipe_nutrition
#   params: ingredients: list[dict]  (each with name, quantity, unit)
#   returns: dict with calories, protein, carbohydrates, fat
#   agent: meal_plan_agent

# Output: app/tools/calculate_nutrition.py
def calculate_recipe_nutrition(ingredients: list[dict]) -> dict:
    """Calculate total calories, protein, carbohydrates, and fat.

    Args:
        ingredients: list of {name, quantity, unit} dicts.

    Returns:
        dict with calories, protein, carbohydrates, fat keys.
    """
    ...

# In app/agents/meal_plan.py:
from app.tools.calculate_nutrition import calculate_recipe_nutrition
Agent(..., tools=[calculate_recipe_nutrition, validate_meal_plan])
```
