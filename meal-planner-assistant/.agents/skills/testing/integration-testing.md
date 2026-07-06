# integration-testing

## Purpose
Write and run integration tests that verify end-to-end agent workflows and tool orchestration, ensuring agents, tools, data stores, and session state work together correctly without mocks for core infrastructure.

## When to Use
- After implementing a new agent or modifying agent instructions
- After changing the workflow or orchestration logic
- Before deploying or packaging — run integration suite to catch regressions
- When a unit test passes but the overall feature doesn't work

## Prerequisites
- Unit tests pass for all individual modules involved
- `pyproject.toml` or `conftest.py` has integration test markers configured
- DuckDB test database is available (or can be created in-memory)
- `rules/domain.md` and `rules/architecture.md` reviewed for workflow contracts

## Inputs
- Agent definitions and tool implementations
- Session state schema and expected data flows
- `session_state` initial data (user profiles, recipes, etc.)

## Expected Outputs
- `tests/test_integration_<feature>.py` file
- Tests that exercise full agent workflows with real tools and a test DuckDB database
- All tests pass with `pytest -m integration tests/`

## Step-by-Step Workflow

1. **Identify critical workflows**: Read agent definitions in `app/agents/` and trace the end-to-end flow. Focus on the main meal planning workflow: Inventory → Recipe → Nutrition → Meal Plan → Shopping List.

2. **Set up test fixtures**: In `tests/conftest.py` or a helper file, create:
   - An in-memory DuckDB instance with test data (user profile, recipes, nutrition data)
   - A pre-populated session state dict with realistic test values
   - Fixtures that initialize the full app context (data stores, tools)

3. **Write workflow test**: Create a test that initializes session state, runs the full workflow (inventory → recipe ranking → meal plan → shopping), and asserts the expected structure at each stage. Use `pytest.mark.integration` decorator.

4. **Test data persistence**: Write a test that sets session state, triggers data store writes, reads back, and verifies the data is correctly persisted in DuckDB.

5. **Test error handling**: Write a test with deliberately bad input (empty inventory, missing profile). Assert the system produces appropriate error messages or fallback behavior without crashing.

6. **Test state transitions**: Verify that session state keys are set and removed according to the workflow. For example, `selected_recipes` should be set after recipe ranking and consumed when `meal_plan` is generated.

7. **Run full suite**: Execute `pytest -m integration tests/ -v` and confirm all tests pass.

## Files to Create or Modify

| Action | File |
|--------|------|
| Create | `tests/test_integration_<feature>.py` — new integration test |
| Modify | `tests/conftest.py` — shared integration test fixtures |

## Validation Checklist
- [ ] Tests marked with `@pytest.mark.integration` (or configured marker)
- [ ] Real tool implementations used (not mocked), only external APIs/Gemini mocked
- [ ] In-memory DuckDB used rather than production database
- [ ] Workflow test passes end-to-end without crashing
- [ ] Error handling test covers: empty inventory, missing profile, missing recipes
- [ ] State transition test verifies session state keys are correctly managed
- [ ] All tests pass with `pytest -m integration tests/`

## Common Mistakes
- Mocking tool implementations — integration tests should call real tools; only mock external API calls (Gemini)
- Using production DuckDB database — always use in-memory or test-specific database
- Writing tests that are too narrow (essentially unit tests with a marker) — integration tests should cover cross-module interactions
- Forgetting lifecycle management — create and teardown DuckDB tables properly in fixtures
- Hardcoding session state expectations that don't match real agent outputs — integration tests should validate structure, not exact values of AI-generated content
- Not handling Gemini API availability — skip integration tests gracefully if API key is missing

## Related Rules
- `rules/domain.md` — session state schema, data store layout
- `rules/architecture.md` — workflow orchestration, agent-tool data flow
- `rules/testing.md` — integration test markers and fixtures

## Example Usage

```python
@pytest.mark.integration
class TestRecipeToShoppingFlow:
    def test_full_workflow(self, session_state, duckdb_test_db):
        # Setup: session_state has user_profile, available_ingredients
        session_state["user_profile"] = {"goal": "weight_loss", ...}
        session_state["available_ingredients"] = [{"name": "chicken", ...}]

        # Run: agents handle ranking, planning, and shopping
        from app.orchestrator import run_workflow_step
        run_workflow_step("recipe_ranking", session_state)
        run_workflow_step("meal_planning", session_state)
        run_workflow_step("shopping_list", session_state)

        # Assert: final state has expected keys
        assert "meal_plan" in session_state
        assert "shopping_list" in session_state
        assert len(session_state["shopping_list"]) > 0
```
