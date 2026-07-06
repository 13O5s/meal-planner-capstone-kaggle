# Workflow Rules

## Purpose

Define the standard development lifecycle and command execution order for this project.

## Principles

- Development follows: lint → test → deploy
- Evaluation follows: generate → grade → analyze → iterate
- Always run `agents-cli install` before first execution in a fresh clone

## Required Practices

### Development order
1. `agents-cli lint` — catches style and type issues
2. `uv run pytest tests/unit tests/integration` — runs all tests
3. If lint fails: `uv run ruff check --fix .` then `uv run ruff format .`
4. Iterate with `agents-cli playground` for interactive testing

### Evaluation loop
1. `agents-cli eval dataset synthesize` — create eval scenarios
2. `agents-cli eval generate` — run agent against eval dataset
3. `agents-cli eval grade` — score agent responses
4. `agents-cli eval analyze` — cluster failure modes
5. Fix issues, rerun generate + grade

### Pre-deployment
- All lint and test commands must pass before deployment
- Deployment requires explicit human approval

## Forbidden Practices

- Skipping lint before commit
- Deploying without running tests
- Changing the `model` value in `Gemini(model=...)` unless explicitly asked
- Running `terraform apply` without `terraform import` on 409 conflicts

## Examples

```bash
# Standard iteration
agents-cli lint
uv run ruff check --fix .
uv run ruff format .
uv run pytest tests/unit tests/integration
agents-cli playground
```
