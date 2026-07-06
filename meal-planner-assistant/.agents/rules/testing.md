# Testing Rules

## Purpose

Establish consistent testing patterns for unit, integration, evaluation, and load testing.

## Principles

- Unit tests cover individual tools and utility functions
- Integration tests cover agent orchestration and end-to-end flows
- Evaluation tests measure agent output quality using LLM-as-judge
- Load tests validate performance under concurrent users

## Required Practices

- Run `uv run pytest tests/unit tests/integration` before deployment
- Unit tests go in `tests/unit/`, integration tests in `tests/integration/`
- Eval datasets go in `tests/eval/datasets/`
- Use `pytest-asyncio` for async test support (loop scope: `function`)
- Test files must be discoverable by pytest (prefix `test_`)
- Mock external dependencies in unit tests

## Forbidden Practices

- Tests that depend on real API keys or network calls (use mocks)
- Skipping tests after code changes
- Adding eval datasets that are not valid JSON
- Committing load test result files (`tests/load_test/.results/` is gitignored)

## Examples

```bash
# Run all tests
uv run pytest tests/unit tests/integration

# Run a single test file
uv run pytest tests/unit/test_dummy.py

# Run eval
agents-cli eval generate
agents-cli eval grade
```
