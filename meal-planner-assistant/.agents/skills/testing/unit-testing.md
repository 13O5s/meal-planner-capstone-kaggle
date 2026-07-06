# unit-testing

## Purpose
Write and organize unit tests for individual tools, services, and classes using pytest, covering normal cases, edge cases, and error conditions with proper mocking of external dependencies.

## When to Use
- Implementing a new tool (gRPC or ADK) and need to verify its logic in isolation
- Adding tests to an existing untested module in `app/tools/` or `app/services/`
- Before refactoring an existing module — write tests first to verify behavior preservation
- After fixing a bug — add a regression test that reproduces the bug and confirms the fix

## Prerequisites
- Module has a clear public API (functions/classes with typed inputs and outputs)
- python-dotenv environment variables available for credentials (loaded via `pytest --override-ini` or conftest)
- `pyproject.toml` or `conftest.py` configured for the project's test runner
- `rules/coding.md` has been reviewed for naming and annotation conventions

## Inputs
- Source module path (e.g., `app/tools/` or `app/services/`)
- Module function signatures and expected behaviors
- Existing test patterns from similar modules in `tests/` directory

## Expected Outputs
- `tests/test_<module>.py` file with pytest test functions
- At minimum: 1 test per public function covering normal case, error case, and edge case
- Mock fixtures for external dependencies (DuckDB, Gemini, file I/O)
- Tests pass when run with `pytest tests/`

## Step-by-Step Workflow

1. **Identify test targets**: List all public functions/classes in the target module that have clear input/output contracts. Focus on pure business logic first — data transformations, validations, calculations.

2. **Review existing tests**: Read `tests/conftest.py` for shared fixtures, `tests/test_*.py` for patterns — mock style (monkeypatch vs unittest.mock), fixture naming conventions, assertion style.

3. **Write mock fixtures**: For each external dependency the module uses (DuckDB connection, Gemini API, file system), create a pytest fixture that replaces it with a mock. Use `pytest.fixture` for setup and `unittest.mock.patch` or monkeypatch for injection.

4. **Write normal-case test**: Call the function with valid, representative inputs. Assert the expected output structure and values. Use `assert` statements with descriptive messages.

5. **Write error-case test**: Call the function with invalid inputs (None, wrong types, empty values). Assert the expected exception is raised with `pytest.raises(ExceptionType)`.

6. **Write edge-case test**: Call with boundary values (0 quantities, empty lists, max values). Assert correct handling — no crashes, sensible defaults or graceful errors.

7. **Organize test classes**: For related tests, group them in a class with `class Test<FeatureName>:`. Use descriptive test function names: `test_<function>_<scenario>`.

8. **Run and verify**: Execute `pytest tests/test_<module>.py -v` and confirm all tests pass. If any fail, fix the code or the test.

## Files to Create or Modify

| Action | File |
|--------|------|
| Create | `tests/test_<module>.py` — new test file |
| Modify | `tests/conftest.py` — if adding shared fixtures |
| Modify | Source module — only if test failures reveal bugs |

## Validation Checklist
- [ ] All public functions have at least one test
- [ ] External dependencies are mocked, never called in real tests
- [ ] Tests cover: normal case, error case, edge case
- [ ] Test functions use descriptive names following `<verb>_<scenario>_<expected>` pattern
- [ ] No side effects between tests (each test is independent)
- [ ] Tests pass with `pytest tests/test_<module>.py -v`
- [ ] No hardcoded secrets or credentials in test files

## Common Mistakes
- Testing implementation details instead of public behavior — test the API contract, not internal helpers (unless they are also public)
- Not mocking external dependencies — tests should never hit real DuckDB or Gemini
- Using monkeypatch where `unittest.mock` is more readable (or vice versa) — follow existing patterns in the project
- Writing overly brittle tests that break on any refactor — prefer black-box testing via the public API
- Skipping edge cases — empty lists, zero values, None inputs, boundary values
- Writing tests that depend on each other — never share mutable state between test functions

## Related Rules
- `rules/coding.md` — naming conventions, type annotations
- `rules/testing.md` — project-specific testing framework and conftest setup

## Example Usage

```python
# app/tools/calculate_nutrition.py has:
def calculate_recipe_nutrition(ingredients: list[dict]) -> dict:
    ...

# tests/test_calculate_nutrition.py:
class TestCalculateRecipeNutrition:
    def test_returns_calories_protein_carbs_fat(self):
        result = calculate_nutrition([{...}])
        assert "calories" in result
        assert "protein" in result

    def test_empty_ingredients_returns_zeros(self):
        assert calculate_nutrition([]) == {"calories": 0, ...}

    def test_unknown_ingredient_skipped_without_error(self):
        result = calculate_nutrition([{"name": "unknown", ...}])
        assert result["calories"] == 0
```
