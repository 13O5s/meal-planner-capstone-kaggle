# test-driven-development

## Purpose
Apply test-driven development (TDD) for new features: write a failing test first, implement the minimal code to pass it, then refactor. This ensures test coverage from the start and produces clean, verifiable implementations.

## When to Use
- Starting a new tool, service, or module
- Adding a feature with a clear contract (known inputs and outputs)
- Any new code that has deterministic logic (not for exploratory or AI-generated code)
- When the user explicitly requests TDD workflow

## Prerequisites
- Feature specification is clear: known inputs, outputs, and behavior for normal and error cases
- pytest is set up and working (`pytest` runs without errors)
- Test file naming convention established (`tests/test_*.py`)
- `rules/coding.md` reviewed for project conventions

## Inputs
- Feature specification or user story
- Expected API (function signatures, classes, data formats)
- Existing code patterns for similar features

## Expected Outputs
- `tests/test_<feature>.py` — test file written (first), then code
- `<feature>.py` implementation that passes all tests
- Clean, refactored code after green phase

## Step-by-Step Workflow

### Phase 1: Red (Write a failing test)

1. **Define the API contract**: Decide the function signature, input types, and return types before writing any implementation code.

2. **Write the test**: Create or update `tests/test_<feature>.py`. Write one test for the normal case (expected behavior). Assert the expected output structure and values.

3. **Run the test**: Execute `pytest tests/test_<feature>.py -v`. Confirm the test fails with an `ImportError` or `NameError` (the module/function doesn't exist yet).

### Phase 2: Green (Make it pass)

4. **Write minimal implementation**: Create the module or function with just enough code to make the test pass. Hardcode return values if needed — the goal is a passing test, not a complete implementation.

5. **Run the test again**: Execute `pytest tests/test_<feature>.py -v`. Confirm it passes. If not, adjust the implementation minimally.

### Phase 3: Refactor (Clean up)

6. **Expand tests**: Add edge-case tests (empty input, boundary values) and error-case tests (invalid input, None). For new edge-case tests, repeat the Red phase: write the test, confirm it fails, implement, confirm it passes.

7. **Refactor implementation**: Clean up the code — extract helper functions, add proper error handling, follow coding conventions. All tests must continue to pass during refactoring.

8. **Final verification**: Run all tests in the test file. Confirm all pass. Run the broader test suite to verify no regressions.

## Files to Create or Modify

| Action | File |
|--------|------|
| Create (first) | `tests/test_<feature>.py` — test file |
| Create (second) | Module file implementing the feature |

## Validation Checklist
- [ ] Test written before implementation code
- [ ] First test run shows RED (failing) before any implementation
- [ ] Minimal implementation makes the test GREEN
- [ ] Refactoring phase does not break existing tests
- [ ] Edge-case tests added during refactoring
- [ ] Error-case tests added during refactoring
- [ ] All tests pass in final verification

## Common Mistakes
- Writing too much implementation code before checking the test — keep the cycle tight (minutes, not hours)
- Skipping the RED phase — writing a test that passes immediately means you're not testing the right thing
- Not refactoring after GREEN — TDD is about clean code, not just passing tests
- Writing tests that are too generic — each test should verify one specific behavior
- Using TDD for non-deterministic code (e.g., Gemini API calls) — TDD works best for pure functions with deterministic inputs and outputs
- Forgetting to run the full suite during refactoring — changes can break other tests

## Related Rules
- `rules/coding.md` — naming, annotations, code conventions
- `rules/testing.md` — test configuration, markers, shared fixtures

## Example Usage

```python
# Step 1 (RED): Write the test first
# tests/test_shopping_list.py
def test_merge_duplicate_ingredients():
    from app.tools.shopping_list import merge_ingredients
    ingredients = [
        {"name": "chicken", "qty": 200, "unit": "g"},
        {"name": "chicken", "qty": 100, "unit": "g"},
    ]
    result = merge_ingredients(ingredients)
    assert result == [{"name": "chicken", "qty": 300, "unit": "g"}]

# Step 2: Run → ImportError (module doesn't exist) → RED ✓

# Step 3 (GREEN): Minimal implementation
# app/tools/shopping_list.py
def merge_ingredients(ingredients):
    return [{"name": "chicken", "qty": 300, "unit": "g"}]

# Step 4: Run → passes → GREEN ✓

# Step 5 (REFACTOR): Full implementation with merging logic
```
