# meal-planner-assistant

ADK 2.0 multi-agent project scaffolded with `agents-cli`. AI-powered meal planning and smart grocery assistant.

## Entrypoints

- `app/__init__.py` exports `app` → the ADK `App` object
- `app/agent.py` defines root `meal_planner_coordinator` Agent + 6 sub-agents, initialized with `Gemini(model="gemini-flash-latest", api_key="AIzaSyD-mock-key-value-12345")`
- `app/fast_api_app.py` is the FastAPI server (loads `.env`, sets up A2A + telemetry + Runner in lifespan)

## Architecture

### Layers

```
Coordinator (instruction prompt)
  │
  ├─ Agents (LLM) ── app/agents/
  │   │
  │   ├─ Tools (deterministic) ── app/tools/
  │   │   │
  │   │   ├─ Services (business logic) ── app/services/
  │   │   │   │
  │   │   │   ├─ Repositories (data access) ── app/database/repositories/
  │   │   │   │   │
  │   │   │   │   ├─ PostgreSQL (via SQLAlchemy async)
  │   │   │   │   └─ In-memory fallback (app/data/stores.py)
```

### Agents

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **Coordinator** | Orchestrates 6-step conditional workflow; delegates via `transfer_to_agent` | — |
| **Profile** | Collects all required fields (age, gender, height, weight, activity, preferences, budget, goal) | `save_profile` |
| **Inventory** | Parses & normalizes user-entered ingredients | `normalize_ingredients` |
| **Recipe** | Searches & ranks recipes by availability, preferences, nutrition | `search_recipes` |
| **Meal Plan + Nutrition** | Generates meal plans, calculates per-meal nutrition, validates against targets | `calculate_recipe_nutrition`, `validate_meal_plan` |
| **Shopping** | Deduplicates, estimates cost, flags budget exceed | `generate_optimized_shopping_list`, `estimate_grocery_cost` |

- **Session state** is the only communication channel: `user_profile`, `available_ingredients`, `selected_recipes`, `meal_plan`, `shopping_list`
- Coordinator checks session state before each step — skips if data already exists.

### Tools (`app/tools/`)

| Tool | File | Calls Service(s) |
|------|------|-------------------|
| `normalize_ingredients` | `normalize_ingredients.py` | `IngredientService.resolve_name` |
| `calculate_recipe_nutrition` | `calculate_nutrition.py` | `NutritionService.calculate` |
| `estimate_grocery_cost` | `cost_estimator.py` | `IngredientService.get_price` |
| `generate_optimized_shopping_list` | `shopping_list.py` | `ShoppingService.generate_shopping_list` |
| `validate_meal_plan` | `meal_plan_validator.py` | `MealPlanService.validate` |
| `save_profile` | `profile_tools.py` | `ProfileService.save_profile` |
| `search_recipes` | `recipe_tools.py` | `RecipeService` + `NutritionService` |

Import pattern: `from app.tools.foo import foo_func` then `tools=[foo_func]`.

### Services (`app/services/`)

| Service | Responsibilities |
|---------|------------------|
| `IngredientService` | `resolve_name`, `get_price`, `get_nutrition`, `get_known_ingredients` |
| `RecipeService` | `search`, `get_all`, `get_by_cuisine`, `get_by_name` |
| `NutritionService` | `calculate` (totals from ingredient list) |
| `ShoppingService` | `generate_shopping_list` (merge + availability deduction) |
| `MealPlanService` | `validate` (10% tolerance check) |
| `ProfileService` | `save_profile`, `get_profile`, `validate_required` |
| `helper` | `optional_session()` — context manager (DB or None) |

All services accept `AsyncSession | None` — they work with or without a database.

### Data Sources

| Source | Contents | Used When |
|--------|----------|-----------|
| `app/data/stores.py` | `RECIPES` (5), `PRICE_DB` (~22), `NUTRITION_DB` (~22) | No DB connected |
| PostgreSQL (20 tables) | Ingredients, recipes, users, nutrition, inventory, shopping history | DB initialized (`is_db_initialized()` = true) |

## Development Phases

### Phase 1: Understand Requirements
Review the agent/tool/data architecture above before writing code. The system runs with PostgreSQL when available, with automatic in-memory fallback.

### Phase 2: Build and Implement
Edit agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop
1. `agents-cli eval dataset synthesize` — create eval scenarios
2. `agents-cli eval generate` — run agent on eval dataset
3. `agents-cli eval grade` — evaluate traces
4. Repeat until satisfied, then use `agents-cli eval compare`, `agents-cli eval analyze`, `agents-cli eval optimize`

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix until all pass.

### Phase 5: Deploy to Dev
**Requires explicit approval.** Run `agents-cli deploy` after confirmation.

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `uv run pytest tests/unit -v` | Run unit tests only |
| `uv run pytest tests/integration -v` | Run integration tests only |
| `agents-cli eval generate` | Run agent on eval dataset, produce traces |
| `agents-cli eval grade` | Run evaluations on traces |
| `agents-cli eval compare` | Compare two grade-results files (regression check) |
| `agents-cli eval analyze` | Cluster failure modes from grade results |
| `agents-cli eval optimize` | Auto-tune agent prompts using eval data |
| `agents-cli lint` | Check code quality (ruff → codespell → ty) |
| `uv run ruff check --fix .` | Auto-fix lint before commit |
| `uv run ruff format .` | Format all files |
| `agents-cli deploy` | Deploy to dev |

## Pre-commit Pipeline

Configured in `.pre-commit-config.yaml` (fail-fast):
1. **ruff** — auto-fix + exit on error
2. **ruff-format** — format check
3. **detect-secrets** — baseline at `.secrets.baseline`
4. **semgrep** — 26 rules (secrets, dangerous Python, ADK architecture)
5–10. **6 validation scripts** in `scripts/`
11. **pytest** — unit tests only
12. **pre-commit-hooks** — trailing-whitespace, EOF, YAML/JSON/TOML check, merge-conflict, detect-private-key
13. **codespell** — ignore list: `rouge`

## Lint & Style Specifics

- `ruff` rules: E, F, W, I, C, B, UP, RUF (line-length 88, target py311). Ignores: E501, C901, B006
- `ruff` isort treats `app`, `frontend` as known-first-party
- `ty` checker ignores most third-party issues (configured in `pyproject.toml`)
- `from typing import Dict, List, Optional, Tuple` is deprecated — use `dict`, `list`, `X | None`, `tuple`

## ADK / SDK Quirks

- `Gemini(model="gemini-flash-latest")` does **not** accept an `api_key` parameter — the Google GenAI SDK reads `GOOGLE_API_KEY` from the environment automatically (set in `.env`, loaded by `load_dotenv()` in `fast_api_app.py`)
- `.env` is gitignored; never put secrets in source code
- For Vertex AI, set `GOOGLE_CLOUD_LOCATION=global` (not `us-east1`) to avoid 404s. Never change the `model` value
- Port 8000 (uvicorn dev) vs 8080 (Docker/ADK web). A2A routes at `/a2a/app`
- Sub-agents inherit the coordinator's model unless explicitly overridden
- **Model 404 errors**: Fix `GOOGLE_CLOUD_LOCATION`, not the model name
- **ADK tool imports**: Import tool instance, not module: `from google.adk.tools.load_web_page import load_web_page`
- Run Python with `uv`: `uv run python script.py`. Run `agents-cli install` first.

## Known Issues (Demo Artifacts — Keep for Security Scanning)

- `app/agent.py` imports `from google.genai import types56` — deliberate scaffold typo (unused, demonstrates pre-commit scanning)
- `app/agent.py` passes `api_key="AIzaSyD-mock-key-value-12345"` to `Gemini` — silently ignored by Pydantic (deliberate security demo artifact for semgrep/detect-secrets)

## Operational Guidelines

- **Code preservation**: Only modify code directly targeted. Preserve surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Stop on repeated errors**: If same error appears 3+ times, fix root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.
