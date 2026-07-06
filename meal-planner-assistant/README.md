# 🥗 Agentic Meal Planner — Backend

Multi-agent meal planning coordinator built on **Google ADK 2.0**, **FastAPI**, and **PostgreSQL**. Generates personalized weekly meal plans with nutrition validation, budget tracking, and optimized shopping lists.

---

## 🛠️ Tech Stack

- **Orchestration**: Google Agent Development Kit (ADK 2.0)
- **API**: FastAPI + WebSockets + A2A protocol
- **Database**: PostgreSQL / SQLAlchemy (async) / Alembic
- **External APIs**: FatSecret Platform API (OAuth 2.0)
- **Protocol**: Model Context Protocol (MCP) for data operations

---

## 📁 Project Structure

```
app/
├── agents/           Sub-agents (profile, recipe, meal_plan)
├── tools/            Deterministic tools (nutrition, validation, shopping)
├── services/         Business logic layer
├── database/
│   ├── models/       8 ORM models → 20 tables
│   ├── repositories/ Data access layer
│   └── seeder.py     Initial data seeding
├── data/stores.py    In-memory fallback (56 ingredients, 5 recipes)
├── fast_api_app.py   FastAPI server (1644 lines)
├── websocket_manager.py
└── workflow_nodes.py Coordinator + function nodes

mcp_servers/
├── profile_mcp/      User profile CRUD tools
└── inventory_mcp/    Ingredient normalization tools

scripts/              Validation scripts (6) + local eval loop
tests/
├── unit/             10 unit tests
├── integration/      4 integration tests
├── load_test/        Locust load test
└── eval/             ADK eval config + 5-case dataset
```

---

## 📋 Prerequisites

- Python 3.11+
- `uv` package manager (`pip install uv`)
- `agents-cli` (optional — `uv sync` is alternative)
- PostgreSQL (optional — falls back to in-memory)

---

## 📦 Installation & Setup

```bash
# Install dependencies
agents-cli install   # or: uv sync

# Environment config
cp .env.example .env
# Then edit .env with your keys
```

### Google Cloud Auth (Vertex AI mode only)

```bash
gcloud auth application-default login
```

### PostgreSQL (optional — in-memory fallback if skipped)

```sql
CREATE DATABASE meal_planner;
```

Fill credentials in `.env`, then (optional) run migrations:

```bash
uv run alembic upgrade head
```

> The app auto-creates all 20 tables and seeds initial data on startup. Alembic is recommended for schema versioning.

### FatSecret API

1. Sign up at [FatSecret Platform API](https://platform.fatsecret.com)
2. Create an app → get Client ID + Client Secret
3. **Register your IP**: Dashboard → My Applications → Edit → Allowed IP Addresses
   - Add `127.0.0.1` (dev), your server IP (prod), or `0.0.0.0/0` (Cloud Run)
4. Set `FATSECRET_CLIENT_ID` and `FATSECRET_CLIENT_SECRET` in `.env`

### Verify

```bash
uv run pytest tests/unit -v
uv run fastapi dev app/fast_api_app.py
curl http://localhost:8000/health
```

---

## 🚀 Usage

| Command | Description |
|---------|-------------|
| `agents-cli playground` | Interactive ADK agent console |
| `uv run fastapi dev app/fast_api_app.py` | Start backend API (port 8000) |
| `uv run adk run meal_planner_workflow` | Run agent via ADK CLI |
| `uv run pytest` | Run all tests |
| `uv run python scripts/validate_mcp.py` | Validate MCP server integrity |

---

## 🏗️ Agent Architecture

```
Coordinator Agent
├── Profile Agent        → save_profile tool
├── Recipe Agent         → search_recipes, calculate_recipe_nutrition
├── Meal Plan Agent      → validate_meal_plan
├── inventory_fn         → normalize_ingredients (deterministic)
├── shopping_fn          → generate_optimized_shopping_list (deterministic)
├── budget_feedback_fn   → RequestInput (human-in-the-loop)
└── done_fn              → Terminates workflow
```

Session state (`user_profile`, `available_ingredients`, `selected_recipes`, `meal_plan`, `shopping_list`) is the only communication channel between steps.

---

## 🔒 Security

- **MCP isolation**: External HTTP calls are forbidden inside agents — all data ops route through MCP servers
- **Input validation**: Rejects out-of-bound values, negative quantities
- **PII redaction**: Scans and masks emails, phones, API keys
- **Allergen gatekeeping**: Zero-tolerance post-check on generated meal plans
- **Macro validation**: ±10% tolerance against user targets

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Add tests and ensure all pass: `uv run pytest`
4. Run lint: `uv run ruff check .`
5. Open a PR
