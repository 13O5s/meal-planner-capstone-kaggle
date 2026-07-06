# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import hashlib
import json
import os
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC
from urllib.parse import quote_plus

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging
from sqlalchemy import text

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

load_dotenv()

_AI_ENABLED = os.environ.get("AI_ENABLED", "false").lower() == "true"

def is_ai_enabled() -> bool:
    return os.environ.get("AI_ENABLED", str(_AI_ENABLED).lower()).lower() == "true"

def set_ai_enabled(val: bool) -> None:
    global _AI_ENABLED
    _AI_ENABLED = val

print(f"[Config] AI_ENABLED={_AI_ENABLED}")

try:
    setup_telemetry()
except Exception:
    pass

try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "local-dev")
    logger = None
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",")
    if os.getenv("ALLOW_ORIGINS")
    else ["http://localhost:5173"]
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_RECIPE_CACHE: dict[str, dict] = {}


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent
    from app.database import close_db, init_db
    from app.database.session import is_db_initialized

    try:
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.database.models import Base
        from app.database.seeder import seed_database
        from app.database.session import get_session_factory

        db_url = os.environ.get("DATABASE_URL") or (
            f"postgresql+asyncpg://{os.environ.get('DB_USER', 'postgres')}"
            f":{quote_plus(os.environ.get('DB_PASSWORD', 'postgres'))}"
            f"@{os.environ.get('DB_HOST', 'localhost')}"
            f":{os.environ.get('DB_PORT', '5432')}"
            f"/{os.environ.get('DB_NAME', 'meal_planner')}"
        )
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Migration: add columns that may be missing on existing tables
            await conn.execute(text(
                "ALTER TABLE saved_plans ADD COLUMN IF NOT EXISTS start_date VARCHAR(10)"
            ))

        init_db(db_url)
        factory = get_session_factory()
        async with factory() as session:
            await seed_database(session)
            await session.commit()
        await engine.dispose()
        print("[DB] PostgreSQL connected and seeded")
    except Exception as e:
        print(f"[DB] PostgreSQL unavailable ({e}), running with in-memory stores")

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield
    if is_db_initialized():
        await close_db()


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.title = "meal-planner-assistant"
app.description = "API for interacting with the Agent meal-planner-assistant"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    if logger is not None:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


def _estimate_cost(ingredients: list[dict]) -> float:
    from app.data.stores import PRICE_DB

    total = 0.0
    for ing in ingredients:
        name = ing.get("name", "").lower().strip()
        qty = ing.get("quantity", 0) or 0
        unit = ing.get("unit", "piece")
        price_info = PRICE_DB.get(name)
        if not price_info:
            continue
        ppu = price_info.get("price_per_unit", 0) or 0
        price_unit = price_info.get("unit", "piece")
        if unit == price_unit:
            total += ppu * qty
        elif unit == "g" and price_unit == "kg":
            total += ppu * qty / 1000
        elif unit == "ml" and price_unit == "L":
            total += ppu * qty / 1000
        elif unit in ("tbsp", "tablespoon") and price_unit in ("L", "ml"):
            total += ppu * qty * 15 / 1000
        else:
            total += ppu * qty
    return round(total, 2)


def _call_gemini(prompt: str) -> tuple[dict | list | None, str | None]:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("[Gemini] No GOOGLE_API_KEY set in environment")
        return None, "No API key configured. Add GOOGLE_API_KEY to .env or update via Settings."
    print(f"[Gemini] Using key ending ...{api_key[-4:]}")
    from google import genai

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text), None
    except Exception as e:
        err_str = str(e)
        if "RESOURCE_EXHAUSTED" in err_str:
            msg = "Gemini quota exhausted (429). Free tier limit reached. Wait for reset or use a paid key."
            print(f"[Gemini] {msg}")
            return None, msg
        elif "API key" in err_str or "not found" in err_str.lower():
            msg = f"Gemini authentication error: {err_str[:120]}"
            print(f"[Gemini] {msg}")
            return None, msg
        else:
            msg = f"Gemini error: {err_str[:200]}"
            print(f"[Gemini] {msg}")
            return None, msg


@app.get("/api/recipes")
async def get_recipes():
    from app.services import NutritionService, RecipeService
    from app.services.helper import optional_session

    async with optional_session() as session:
        recipe_service = RecipeService(session)
        nutrition_service = NutritionService(session)
        recipes_data = await recipe_service.get_all()

    result = []
    for r in recipes_data:
        ingredients = r.get("ingredients", [])
        nutrition = r.get("nutrition")
        if not nutrition:
            nutrition = await nutrition_service.calculate(ingredients)

        total_time = (r.get("prep_time_minutes", 0) or 0) + (r.get("cook_time_minutes", 0) or 0)
        num_ingredients = len(ingredients)
        difficulty = "easy"
        if total_time >= 30 and num_ingredients >= 8:
            difficulty = "hard"
        elif total_time > 15 or num_ingredients > 4:
            difficulty = "medium"

        tags = []
        cuisine = r.get("cuisine", "") or ""
        cuisines_lower = cuisine.lower()
        if "health" in cuisines_lower:
            tags.append("healthy")
        elif "italian" in cuisines_lower:
            tags.append("italian")
        elif "asian" in cuisines_lower:
            tags.append("asian")
        if "protein" in cuisines_lower:
            tags.append("high-protein")
        if nutrition and nutrition.get("calories", 0) < 350:
            tags.append("low-calorie")
        if nutrition and nutrition.get("protein", 0) >= 30:
            tags.append("high-protein")
        if total_time <= 20:
            tags.append("quick")

        instructions_text = r.get("instructions", "") or ""
        if isinstance(instructions_text, str):
            instructions_list = [s.strip() for s in instructions_text.replace("\n", ".").split(".") if s.strip()]
        else:
            instructions_list = list(instructions_text)

        recipe_id = hashlib.md5(r.get("name", "").encode()).hexdigest()[:8]
        result.append({
            "id": recipe_id,
            "title": r.get("name", ""),
            "cooking_time": total_time,
            "calories": nutrition.get("calories", 0) if nutrition else 0,
            "protein": nutrition.get("protein", 0) if nutrition else 0,
            "carbs": nutrition.get("carbohydrates", 0) if nutrition else 0,
            "fat": nutrition.get("fat", 0) if nutrition else 0,
            "difficulty": difficulty,
            "estimated_cost": _estimate_cost(ingredients),
            "cuisine": cuisine or "General",
            "ingredients": [
                {"name": i["name"], "quantity": i["quantity"], "unit": i["unit"], "available": True}
                for i in ingredients
            ],
            "instructions": instructions_list,
            "tags": tags,
        })

    return result


@app.get("/api/ingredients")
async def get_ingredients():
    from app.data.stores import NUTRITION_DB, PRICE_DB
    from app.services.helper import optional_session
    from app.services.ingredient_service import IngredientService

    async with optional_session() as session:
        service = IngredientService(session)
        names = await service.get_known_ingredients()

    result = []
    for name in sorted(names):
        price = PRICE_DB.get(name, {})
        nutrition = NUTRITION_DB.get(name, {})
        result.append({
            "name": name,
            "category": price.get("category", "unknown"),
            "unit": price.get("unit", "piece"),
            "price_per_unit": price.get("price_per_unit", 0),
            "nutrition": nutrition,
        })

    return result


@app.post("/api/ingredients/lookup-nutrition")
async def lookup_nutrition(data: dict):
    from app.data.stores import NUTRITION_DB

    name = (data.get("name", "") or "").strip().lower()
    if not name:
        return {"name": name, "nutrition": None, "error": "No name provided"}

    cached = NUTRITION_DB.get(name)
    if cached:
        return {"name": name, "nutrition": dict(cached)}

    prompt = (
        f'You are a food nutrition database. For the food "{name}", return ONLY valid JSON with exactly these keys:\n'
        '{\n'
        '  "calories_per_100g": <number>,\n'
        '  "protein_per_100g": <number>,\n'
        '  "carbs_per_100g": <number>,\n'
        '  "fat_per_100g": <number>\n'
        '}\n'
        "Use realistic values per 100g. If the food is a liquid, estimate per 100ml. "
        "Return ONLY the JSON object, no markdown, no explanation."
    )
    result, error = _call_gemini(prompt)
    if error or not isinstance(result, dict):
        return {"name": name, "nutrition": None, "error": error or "Invalid response from Gemini"}

    nutrition = {
        "calories_per_100g": float(result.get("calories_per_100g", 0)),
        "protein_per_100g": float(result.get("protein_per_100g", 0)),
        "carbs_per_100g": float(result.get("carbs_per_100g", 0)),
        "fat_per_100g": float(result.get("fat_per_100g", 0)),
    }
    NUTRITION_DB[name] = nutrition
    return {"name": name, "nutrition": nutrition, "error": None}


# ── FatSecret API proxy endpoints ─────────────────────────────────────────────


@app.post("/api/fatsecret/search")
async def fatsecret_search(data: dict):
    """Search FatSecret foods for autocomplete suggestions.

    Body: {"query": "chicken breast", "max_results": 8}
    Returns: list of {food_id, name, brand, food_type, nutrition}
    """
    from app.services.fatsecret_service import search_foods

    query = (data.get("query", "") or "").strip()
    max_results = min(int(data.get("max_results", 8)), 20)

    if not query:
        return {"results": [], "error": "No query provided"}

    results = await search_foods(query, max_results=max_results)
    return {"results": results, "query": query}


@app.get("/api/fatsecret/food/{food_id}")
async def fatsecret_get_food(food_id: str):
    """Get detailed nutrition info for a specific FatSecret food by its ID.

    Returns: {food_id, name, brand, food_type, category, nutrition}
    """
    from app.services.fatsecret_service import get_food_by_id

    food_id = food_id.strip()
    if not food_id:
        return {"error": "No food_id provided", "food": None}

    food = await get_food_by_id(food_id)
    if not food:
        return {"error": "Food not found", "food": None}

    return {"food": food}


@app.post("/api/auth/register")
async def register(data: dict):
    from app.database.session import is_db_initialized

    email = (data.get("email", "") or "").strip().lower()
    password = data.get("password", "") or ""
    if not email or not password:
        return {"success": False, "error": "Email and password required"}

    if is_db_initialized():
        from app.database.repositories.user_repo import UserRepository
        from app.database.session import get_session

        async with get_session() as session:
            repo = UserRepository(session)
            existing = await repo.find_by_email(email)
            if existing:
                return {"success": False, "error": "Email already registered"}
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = await repo.create(email=email, password_hash=password_hash)
            await session.commit()
            return {
                "success": True,
                "user_id": str(user.id),
                "profile_complete": False,
            }

    from app.data.stores import USERS

    if email in USERS:
        return {"success": False, "error": "Email already registered"}
    user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
    USERS[email] = {
        "user_id": user_id,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "profile_complete": False,
    }
    return {"success": True, "user_id": user_id, "profile_complete": False}


@app.post("/api/auth/login")
async def login(data: dict):
    from app.database.session import is_db_initialized

    email = (data.get("email", "") or "").strip().lower()
    password = data.get("password", "") or ""

    if is_db_initialized():
        from app.database.repositories.user_repo import UserRepository
        from app.database.session import get_session
        from app.services.profile_service import ProfileService

        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.find_by_email(email)
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            if user.password_hash != hashlib.sha256(password.encode()).hexdigest():
                return {"success": False, "error": "Invalid email or password"}

            profile = await repo.get_profile(user.id)
            profile_complete = profile is not None
            profile_data = None
            if profile:
                service = ProfileService(session)
                profile_data = await service.get_profile(str(user.id))

            return {
                "success": True,
                "user_id": str(user.id),
                "email": email,
                "profile_complete": profile_complete,
                "profile": profile_data,
            }

    from app.data.stores import PROFILES, USERS

    user = USERS.get(email)
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    if user["password_hash"] != hashlib.sha256(password.encode()).hexdigest():
        return {"success": False, "error": "Invalid email or password"}
    profile_complete = user.get("profile_complete", False)
    profile_data = PROFILES.get(user["user_id"], None) if profile_complete else None
    return {
        "success": True,
        "user_id": user["user_id"],
        "email": email,
        "profile_complete": profile_complete,
        "profile": profile_data,
    }


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    import uuid

    from app.database.session import is_db_initialized

    if is_db_initialized():
        from app.database.repositories.user_repo import UserRepository
        from app.database.session import get_session
        from app.services.profile_service import ProfileService

        async with get_session() as session:
            try:
                uid = uuid.UUID(user_id)
            except ValueError:
                return {"success": False, "error": f"Invalid user_id format: {user_id}"}
            repo = UserRepository(session)
            profile = await repo.get_profile(uid)
            if profile is None:
                return {"success": False, "error": "Profile not found"}
            service = ProfileService(session)
            profile_data = await service.get_profile(user_id)
            return {"success": True, "profile": profile_data}

    from app.data.stores import PROFILES

    profile = PROFILES.get(user_id)
    if profile is None:
        return {"success": False, "error": "Profile not found"}
    return {"success": True, "profile": profile}


@app.post("/api/profile")
async def save_profile(data: dict):
    from app.database.session import is_db_initialized

    user_id = data.get("user_id", "") or ""
    if not user_id:
        return {"success": False, "error": "user_id required"}

    if is_db_initialized():
        from app.services.helper import optional_session
        from app.services.profile_service import ProfileService

        async with optional_session() as session:
            service = ProfileService(session)
            try:
                result = await service.save_profile(data)
                if session:
                    await session.commit()
                return result
            except Exception as e:
                if session:
                    await session.rollback()
                return {"success": False, "error": str(e)}

    from app.data.stores import PROFILES, USERS

    save_data = {k: v for k, v in data.items() if k != "user_id"}
    PROFILES[user_id] = save_data
    for email, u in USERS.items():
        if u["user_id"] == user_id:
            u["profile_complete"] = True
            break
    return {"success": True, "user_id": user_id, "fields_saved": list(save_data.keys())}


@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    from datetime import datetime, timedelta

    from app.database.session import is_db_initialized

    cut_off = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if is_db_initialized():
        return await _get_history_db(user_id, cut_off)
    return _get_history_memory(user_id, cut_off)


def _get_history_memory(user_id: str, cut_off: str) -> list[dict]:
    from datetime import datetime

    from app.data.stores import MEAL_PLANS, SHOPPING_ITEMS, SHOPPING_LISTS

    entries: list[dict] = []
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Meal plans: created before now AND within 30 days
    plans = MEAL_PLANS.get(user_id, [])
    kept_plans = []
    for plan in plans:
        created = plan.get("created_at", "")
        if created > now_str:
            kept_plans.append(plan)
        elif created >= cut_off:
            kept_plans.append(plan)
            entries.append({
                "id": plan["id"],
                "type": "meal_plan",
                "title": f"{plan.get('strategy', 'Balanced').capitalize()} Meal Plan ({plan.get('numDays', 0)} days)",
                "created_at": created,
                "data": plan,
            })
    MEAL_PLANS[user_id] = kept_plans

    # Shopping lists: with purchased items AND within 30 days
    lists = SHOPPING_LISTS.get(user_id, [])
    kept_lists = []
    for sl in lists:
        created = sl.get("created_at", "")
        if created < cut_off:
            SHOPPING_ITEMS.pop(sl["id"], None)
            continue
        kept_lists.append(sl)
        items = SHOPPING_ITEMS.get(sl["id"], [])
        purchased = [it for it in items if it.get("purchased")]
        if purchased:
            entries.append({
                "id": sl["id"],
                "type": "shopping_list",
                "title": f"Shopping List ({len(purchased)} item{'s' if len(purchased) > 1 else ''} purchased)",
                "created_at": created,
                "data": {
                    "plan_id": sl.get("plan_id"),
                    "total_items": len(items),
                    "purchased_count": len(purchased),
                    "purchased_items": purchased,
                },
            })
    SHOPPING_LISTS[user_id] = kept_lists

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries


async def _get_history_db(user_id: str, cut_off: str) -> list[dict]:
    from datetime import datetime

    from sqlalchemy import delete, select

    from app.database.models.saved_plan import SavedPlan
    from app.database.models.saved_shopping import SavedShoppingItem, SavedShoppingList
    from app.database.session import get_session

    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries: list[dict] = []

    async with get_session() as session:
        # Meal plans: created before now AND within 30 days
        result = await session.execute(
            select(SavedPlan).where(
                SavedPlan.user_id == user_id,
                SavedPlan.created_at >= cut_off,
                SavedPlan.created_at <= now_str,
            ).order_by(SavedPlan.created_at.desc())
        )
        for row in result.scalars().all():
            plan = {
                "id": row.id,
                "strategy": row.strategy,
                "numDays": row.num_days,
                "days": json.loads(row.days_json),
                "start_date": row.start_date,
                "created_at": row.created_at,
            }
            entries.append({
                "id": row.id,
                "type": "meal_plan",
                "title": f"{row.strategy.capitalize()} Meal Plan ({row.num_days} days)",
                "created_at": row.created_at,
                "data": plan,
            })

        # Shopping lists: with purchased items AND within 30 days
        list_result = await session.execute(
            select(SavedShoppingList).where(
                SavedShoppingList.user_id == user_id,
                SavedShoppingList.created_at >= cut_off,
            ).order_by(SavedShoppingList.created_at.desc())
        )
        for sl in list_result.scalars().all():
            items_result = await session.execute(
                select(SavedShoppingItem).where(
                    SavedShoppingItem.list_id == sl.id,
                    SavedShoppingItem.purchased == True,
                )
            )
            purchased = []
            for row in items_result.scalars().all():
                purchased.append({
                    "id": row.id,
                    "ingredient_name": row.ingredient_name,
                    "total_quantity": row.total_quantity,
                    "unit": row.unit,
                    "estimated_cost": row.estimated_cost,
                    "category": row.category,
                })
            if purchased:
                entries.append({
                    "id": sl.id,
                    "type": "shopping_list",
                    "title": f"Shopping List ({len(purchased)} item{'s' if len(purchased) > 1 else ''} purchased)",
                    "created_at": sl.created_at,
                    "data": {
                        "plan_id": sl.plan_id,
                        "total_items": 0,
                        "purchased_count": len(purchased),
                        "purchased_items": purchased,
                    },
                })

        # Cleanup: delete plans and shopping lists older than 30 days
        await session.execute(
            delete(SavedPlan).where(
                SavedPlan.user_id == user_id,
                SavedPlan.created_at < cut_off,
            )
        )

        old_list_ids = [
            r[0] for r in (
                await session.execute(
                    select(SavedShoppingList.id).where(
                        SavedShoppingList.user_id == user_id,
                        SavedShoppingList.created_at < cut_off,
                    )
                )
            ).all()
        ]
        if old_list_ids:
            await session.execute(
                delete(SavedShoppingItem).where(
                    SavedShoppingItem.list_id.in_(old_list_ids)
                )
            )
            await session.execute(
                delete(SavedShoppingList).where(
                    SavedShoppingList.id.in_(old_list_ids)
                )
            )
        await session.commit()

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries


# ── Recipe Detail (MUST be before parameterized routes) ─────────────────


@app.post("/api/meal-plans/generate-recipe-detail")
async def generate_recipe_detail(data: dict):
    meal_name = data.get("meal_name", "")
    meal_type = data.get("meal_type", "Meal")
    strategy = data.get("strategy", "balanced")
    cache_key = f"{meal_name}|{meal_type}"

    cached = _RECIPE_CACHE.get(cache_key)
    if cached:
        return {"success": True, "recipe": dict(cached), "cached": True}

    prompt = f"""You are a recipe assistant. Generate a detailed recipe for "{meal_name}" ({meal_type}) as part of a "{strategy}" meal plan.
Return ONLY valid JSON object, no other text:
{{
  "ingredients": [
    {{"name": "ingredient name", "quantity": 200, "unit": "g"}},
    ...
  ],
  "instructions": [
    "Step 1: ...",
    "Step 2: ...",
    ...
  ],
  "nutrition": {{"calories": 400, "protein": 25, "carbs": 30, "fat": 15}}
}}
Include 5-8 ingredients and 4-6 instruction steps. Make the recipe realistic and achievable."""

    if is_ai_enabled():
        result, err = _call_gemini(prompt)
        if err or not result or not isinstance(result, dict):
            return {"success": False, "error": err or "AI returned invalid data"}
        _RECIPE_CACHE[cache_key] = result
        return {"success": True, "recipe": result}

    from app.data.static_ai_data import get_fallback_recipe
    result = get_fallback_recipe(meal_name, meal_type)
    _RECIPE_CACHE[cache_key] = result
    return {"success": True, "recipe": result}


@app.post("/api/recipes/resolve-ingredients")
async def resolve_meal_ingredients(data: dict):
    meal_name = data.get("meal_name", "")
    meal_type = data.get("meal_type", "Meal")
    if not meal_name:
        return {"success": False, "ingredients": []}
    from app.data.static_ai_data import get_fallback_recipe
    recipe = get_fallback_recipe(meal_name, meal_type)
    return {"success": True, "ingredients": recipe.get("ingredients", [])}


# ── Meal Plan CRUD ──────────────────────────────────────────────────────


def _plan_to_db(user_id: str, plan: dict) -> dict:
    return {
        "id": plan["id"],
        "user_id": user_id,
        "strategy": plan.get("strategy", "balanced"),
        "num_days": plan.get("numDays", 7),
        "days_json": json.dumps(plan.get("days", [])),
        "start_date": plan.get("start_date"),
        "created_at": plan.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    }


def _plan_from_db(row) -> dict:
    return {
        "id": row.id,
        "strategy": row.strategy,
        "numDays": row.num_days,
        "days": json.loads(row.days_json),
        "start_date": row.start_date,
        "created_at": row.created_at,
    }


async def _get_plans_from_db(user_id: str) -> list[dict]:
    from sqlalchemy import select

    from app.database.models.saved_plan import SavedPlan
    from app.database.session import get_session

    async with get_session() as session:
        result = await session.execute(
            select(SavedPlan).where(SavedPlan.user_id == user_id).order_by(SavedPlan.created_at.desc())
        )
        return [_plan_from_db(row) for row in result.scalars().all()]


async def _save_plan_to_db(user_id: str, plan: dict) -> None:
    from app.database.models.saved_plan import SavedPlan
    from app.database.session import get_session

    async with get_session() as session:
        db_plan = SavedPlan(**_plan_to_db(user_id, plan))
        session.add(db_plan)
        await session.commit()


async def _update_plan_in_db(plan_id: str, data: dict) -> bool:
    from sqlalchemy import update

    from app.database.models.saved_plan import SavedPlan
    from app.database.session import get_session

    async with get_session() as session:
        upd = {k: v for k, v in data.items() if k not in ("id", "user_id")}
        if "days" in upd:
            upd["days_json"] = json.dumps(upd.pop("days"))
        if "numDays" in upd:
            upd["num_days"] = upd.pop("numDays")
        if not upd:
            return True
        stmt = update(SavedPlan).where(SavedPlan.id == plan_id).values(**upd)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0


async def _delete_plan_from_db(plan_id: str) -> bool:
    from sqlalchemy import delete

    from app.database.models.saved_plan import SavedPlan
    from app.database.session import get_session

    async with get_session() as session:
        stmt = delete(SavedPlan).where(SavedPlan.id == plan_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0


def _get_plan_from_memory(user_id: str, plan_id: str) -> dict | None:
    from app.data.stores import MEAL_PLANS

    plans = MEAL_PLANS.get(user_id, [])
    return next((p for p in plans if p["id"] == plan_id), None)


def _ensure_memory_store(user_id: str) -> None:
    from app.data.stores import MEAL_PLANS

    if user_id not in MEAL_PLANS:
        MEAL_PLANS[user_id] = []


@app.get("/api/meal-plans/{user_id}")
async def get_meal_plans(user_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        plans = await _get_plans_from_db(user_id)
        return {"success": True, "plans": plans}

    from app.data.stores import MEAL_PLANS

    plans = MEAL_PLANS.get(user_id, [])
    return {"success": True, "plans": list(reversed(plans))}


@app.post("/api/generate-meal-plan")
async def generate_meal_plan(data: dict):
    strategy = data.get("strategy", "Budget")
    num_days = data.get("numDays", 7)
    start_date = data.get("startDate", "")
    profile = data.get("userProfile", {})

    profile_hint = ""
    if profile:
        goal = profile.get("goal", "")
        calorie_target = profile.get("calorie_target", "")
        diet = profile.get("dietary_preferences", "")
        budget = profile.get("budget", "")
        profile_hint = (
            f"User goal: {goal}. "
            f"Calorie target: {calorie_target}. "
            f"Diet: {diet}. "
            f"Budget: ${budget}/week. "
        )

    prompt = (
        f"Generate a {num_days}-day {strategy.lower()} meal plan starting from {start_date}. "
        f"{profile_hint}"
        f"Each day must have exactly 3 meals (Breakfast, Lunch, Dinner). "
        f"Return ONLY valid JSON array — no markdown, no code fences. "
        f"Format: "
        f'[{{"day":"Monday","meals":[{{"type":"Breakfast","name":"...","calories":350,"protein":20,"carbs":45,"fat":12,"time":"15 min","cost":3.50}},{{"type":"Lunch",...}},{{"type":"Dinner",...}}]}}]'
    )

    result, error = _call_gemini(prompt)
    if error:
        return {"success": False, "error": error}
    if not result or not isinstance(result, list):
        return {"success": False, "error": "AI returned invalid data"}
    return {"success": True, "days": result, "error": None}


@app.post("/api/meal-plans/{user_id}")
async def create_meal_plan(user_id: str, data: dict):
    from app.database.session import is_db_initialized

    days = data.get("days", [])
    if not days or not isinstance(days, list) or len(days) == 0:
        return {"success": False, "error": "No meal data in plan — generation may have failed due to AI quota limits. Please try again later."}

    plan = {
        "id": uuid.uuid4().hex[:8],
        "strategy": data.get("strategy", "balanced"),
        "numDays": data.get("numDays", 7),
        "days": days,
        "start_date": data.get("start_date"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if is_db_initialized():
        await _save_plan_to_db(user_id, plan)
    else:
        _ensure_memory_store(user_id)
        from app.data.stores import MEAL_PLANS

        MEAL_PLANS[user_id].append(plan)

    await _emit_notification(
        user_id,
        "meal_plan_ready",
        "Meal Plan Ready",
        f"Your {plan.get('strategy', 'balanced').capitalize()} meal plan ({plan.get('numDays', 0)} days) has been created.",
    )

    return {"success": True, "plan": plan}


@app.put("/api/meal-plans/{user_id}/{plan_id}")
async def update_meal_plan(user_id: str, plan_id: str, data: dict):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        ok = await _update_plan_in_db(plan_id, data)
        if not ok:
            return {"success": False, "error": "Plan not found"}
        return {"success": True, "plan": data}

    from app.data.stores import MEAL_PLANS

    plans = MEAL_PLANS.get(user_id, [])
    for i, p in enumerate(plans):
        if p["id"] == plan_id:
            p.update({k: v for k, v in data.items() if k != "id"})
            plans[i] = p
            return {"success": True, "plan": p}
    return {"success": False, "error": "Plan not found"}


@app.delete("/api/meal-plans/{user_id}/{plan_id}")
async def delete_meal_plan(user_id: str, plan_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        ok = await _delete_plan_from_db(plan_id)
        return {"success": ok, "error": "" if ok else "Plan not found"}

    from app.data.stores import MEAL_PLANS

    plans = MEAL_PLANS.get(user_id, [])
    for i, p in enumerate(plans):
        if p["id"] == plan_id:
            plans.pop(i)
            return {"success": True}
    return {"success": False, "error": "Plan not found"}


@app.post("/api/meal-plans/{user_id}/{plan_id}/regenerate-day")
async def regenerate_day(user_id: str, plan_id: str, data: dict):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        plan = None
        db_plans = await _get_plans_from_db(user_id)
        plan = next((p for p in db_plans if p["id"] == plan_id), None)
    else:
        plan = _get_plan_from_memory(user_id, plan_id)

    if not plan:
        return {"success": False, "error": "No meal plan data available, please generate a new meal plan."}

    day_index = data.get("day_index", 0)
    days = plan.get("days", [])
    if not days:
        return {"success": False, "error": "No meal data available, please generate a new meal plan."}
    if day_index < 0 or day_index >= len(days):
        return {"success": False, "error": "Invalid day_index"}

    day = days[day_index]
    day_name = day.get("day", f"Day {day_index + 1}")
    strategy = plan.get("strategy", "balanced")

    prompt = f"""You are a meal planning assistant. Generate 3 meals for {day_name} as part of a "{strategy}" meal plan.
Return ONLY valid JSON array, no other text:
[
  {{"type": "Breakfast", "name": "...", "calories": 350, "protein": 20, "carbs": 45, "fat": 12, "time": "15 min", "cost": 3.50}},
  {{"type": "Lunch", "name": "...", "calories": 550, "protein": 35, "carbs": 50, "fat": 18, "time": "25 min", "cost": 5.00}},
  {{"type": "Dinner", "name": "...", "calories": 650, "protein": 40, "carbs": 55, "fat": 22, "time": "40 min", "cost": 7.00}}
]
Make each meal realistic with appropriate macros for the meal type."""

    if is_ai_enabled():
        meals, err = _call_gemini(prompt)
        if err or not meals or not isinstance(meals, list):
            return {"success": False, "error": err or "AI returned invalid data"}
    else:
        from app.data.static_ai_data import get_fallback_day
        meals = get_fallback_day(day_name)["meals"]

    days[day_index]["meals"] = meals
    plan["days"] = days

    if is_db_initialized():
        await _update_plan_in_db(plan_id, {"days": days})
    else:
        stored = _get_plan_from_memory(user_id, plan_id)
        if stored:
            stored["days"] = days

    return {"success": True, "day": days[day_index]}


@app.post("/api/meal-plans/{user_id}/{plan_id}/replace-meal")
async def replace_meal(user_id: str, plan_id: str, data: dict):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        db_plans = await _get_plans_from_db(user_id)
        plan = next((p for p in db_plans if p["id"] == plan_id), None)
    else:
        plan = _get_plan_from_memory(user_id, plan_id)

    if not plan:
        return {"success": False, "error": "No meal plan data available, please generate a new meal plan."}

    day_index = data.get("day_index", 0)
    meal_index = data.get("meal_index", 0)
    days = plan.get("days", [])
    if not days:
        return {"success": False, "error": "No meal data available, please generate a new meal plan."}
    if day_index < 0 or day_index >= len(days):
        return {"success": False, "error": "Invalid day_index"}

    meals = days[day_index].get("meals", [])
    if meal_index < 0 or meal_index >= len(meals):
        return {"success": False, "error": "Invalid meal_index"}

    original = meals[meal_index]
    day_name = days[day_index].get("day", f"Day {day_index + 1}")
    strategy = plan.get("strategy", "balanced")
    meal_type = original.get("type", "Meal")
    original_name = original.get("name", "")

    prompt = f"""You are a meal planning assistant. Suggest a replacement for the {meal_type} "{original_name}" in a "{strategy}" meal plan for {day_name}.
Return ONLY valid JSON object, no other text:
{{"type": "{meal_type}", "name": "...", "calories": 400, "protein": 25, "carbs": 30, "fat": 15, "time": "20 min", "cost": 4.50}}
The replacement should be different from the original but fit the same meal type."""

    if is_ai_enabled():
        new_meal, err = _call_gemini(prompt)
        if err or not new_meal or not isinstance(new_meal, dict):
            return {"success": False, "error": err or "AI returned invalid data"}
    else:
        from app.data.static_ai_data import get_fallback_meal
        new_meal = get_fallback_meal(meal_type, original_name)

    meals[meal_index] = new_meal
    days[day_index]["meals"] = meals
    plan["days"] = days

    if is_db_initialized():
        await _update_plan_in_db(plan_id, {"days": days})
    else:
        stored = _get_plan_from_memory(user_id, plan_id)
        if stored:
            stored["days"] = days

    return {"success": True, "meal": new_meal}


# ── Shopping List ──────────────────────────────────────────────────────


def _ingredients_from_plan(plan: dict) -> list[dict]:
    from app.data.static_ai_data import get_fallback_recipe

    aggregated: dict[str, dict] = {}
    for day in plan.get("days", []):
        for meal in day.get("meals", []):
            recipe = get_fallback_recipe(meal.get("name", ""), meal.get("type", "Meal"))
            for ing in recipe.get("ingredients", []):
                name = ing.get("name", "").lower().strip()
                qty = float(ing.get("quantity", 0) or 0)
                unit = ing.get("unit", "piece")
                key = f"{name}|{unit}"
                if key in aggregated:
                    aggregated[key]["quantity"] += qty
                else:
                    aggregated[key] = {"name": name, "quantity": qty, "unit": unit}
    return list(aggregated.values())


async def _save_shopping_list_db(user_id: str, plan_id: str, items: list[dict]) -> dict:
    from sqlalchemy import delete, select

    from app.database.models.saved_shopping import SavedShoppingItem, SavedShoppingList
    from app.database.session import get_session

    list_id = uuid.uuid4().hex[:8]
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    async with get_session() as session:
        await session.execute(delete(SavedShoppingItem).where(
            SavedShoppingItem.list_id.in_(
                select(SavedShoppingList.id).where(SavedShoppingList.user_id == user_id)
            )
        ))
        await session.execute(delete(SavedShoppingList).where(SavedShoppingList.user_id == user_id))

        sl = SavedShoppingList(id=list_id, user_id=user_id, plan_id=plan_id, created_at=created_at)
        session.add(sl)

        for it in items:
            si = SavedShoppingItem(
                id=uuid.uuid4().hex[:8],
                list_id=list_id,
                ingredient_name=it["ingredient_name"],
                total_quantity=it["total_quantity"],
                unit=it["unit"],
                estimated_cost=it["estimated_cost"],
                category=it["category"],
                already_have=it["already_have"],
                need=it["need"],
                purchased=False,
            )
            session.add(si)
        await session.commit()

    return {"id": list_id, "plan_id": plan_id, "created_at": created_at, "items": items}


def _save_shopping_list_memory(user_id: str, plan_id: str, items: list[dict]) -> dict:
    from app.data.stores import SHOPPING_ITEMS, SHOPPING_LISTS

    list_id = uuid.uuid4().hex[:8]
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    SHOPPING_LISTS[user_id] = [{"id": list_id, "plan_id": plan_id, "created_at": created_at}]
    SHOPPING_ITEMS[list_id] = [
        {**it, "id": uuid.uuid4().hex[:8], "list_id": list_id, "purchased": False}
        for it in items
    ]
    return {"id": list_id, "plan_id": plan_id, "created_at": created_at, "items": items}


@app.post("/api/meal-plans/{user_id}/{plan_id}/apply-shopping-list")
async def apply_shopping_list(user_id: str, plan_id: str, data: dict = {}):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        db_plans = await _get_plans_from_db(user_id)
        plan = next((p for p in db_plans if p["id"] == plan_id), None)
    else:
        plan = _get_plan_from_memory(user_id, plan_id)

    if not plan:
        return {"success": False, "error": "Plan not found"}

    needed = _ingredients_from_plan(plan)
    inventory = data.get("inventory", [])

    inventory_map: dict[str, list[dict]] = {}
    for inv in inventory:
        name = inv.get("name", "").lower().strip()
        if name:
            inventory_map.setdefault(name, []).append(inv)

    def _convert_qty(qty: float, from_unit: str, to_unit: str) -> float:
        if from_unit == to_unit:
            return qty
        if from_unit == "kg" and to_unit == "g":
            return qty * 1000
        if from_unit == "g" and to_unit == "kg":
            return qty / 1000
        if from_unit == "L" and to_unit == "ml":
            return qty * 1000
        if from_unit == "ml" and to_unit == "L":
            return qty / 1000
        if from_unit == "piece" and to_unit == "g":
            return qty * 200
        if from_unit == "g" and to_unit == "piece":
            return qty / 200
        return qty

    from app.data.stores import PRICE_DB

    items = []
    for ing in needed:
        name = ing["name"]
        inv_list = inventory_map.get(name)
        have = 0.0
        if inv_list:
            for inv_item in inv_list:
                inv_qty = float(inv_item.get("quantity", 0) or 0)
                inv_unit = inv_item.get("unit", "piece")
                have += _convert_qty(inv_qty, inv_unit, ing["unit"])

        need = max(0, ing["quantity"] - have)
        if need < 0.01:
            continue

        price_info = PRICE_DB.get(name, {})
        ppu = float(price_info.get("price_per_unit", 0) or 0)
        price_unit = price_info.get("unit", ing["unit"])
        cost = ppu * need
        if ing["unit"] == "g" and price_unit == "kg":
            cost = ppu * need / 1000
        elif ing["unit"] == "ml" and price_unit == "L":
            cost = ppu * need / 1000

        items.append({
            "ingredient_name": name,
            "total_quantity": ing["quantity"],
            "unit": ing["unit"],
            "estimated_cost": round(cost, 2),
            "category": price_info.get("category", "unknown"),
            "already_have": round(have, 2),
            "need": round(need, 2),
        })

    items.sort(key=lambda x: x["category"])

    if is_db_initialized():
        result = await _save_shopping_list_db(user_id, plan_id, items)
    else:
        result = _save_shopping_list_memory(user_id, plan_id, items)

    total_cost = sum(it["estimated_cost"] for it in items)

    budget = None
    if is_db_initialized():
        from app.database.repositories.user_repo import UserRepository
        from app.database.session import get_session
        from app.services.profile_service import ProfileService

        try:
            async with get_session() as session:
                repo = UserRepository(session)
                profile = await repo.get_profile(uuid.UUID(user_id))
                if profile:
                    service = ProfileService(session)
                    profile_data = await service.get_profile(user_id)
                    budget = profile_data.get("budget")
        except Exception:
            pass
    else:
        from app.data.stores import PROFILES

        profile_data = PROFILES.get(user_id, {})
        budget = profile_data.get("budget")

    budget_val = None
    if budget is not None:
        try:
            budget_val = float(str(budget).replace("$", "").strip())
        except (ValueError, TypeError):
            pass

    if budget_val is not None and total_cost > budget_val:
        await _emit_notification(
            user_id,
            "budget_update",
            "Budget Update",
            f"Shopping list (${total_cost:.2f}) exceeds your weekly budget of ${budget_val:.2f}.",
        )

    return {
        "success": True,
        "shopping_list": result,
        "total_cost": round(total_cost, 2),
        "plan_summary": {"numDays": plan.get("numDays", 0), "numMeals": sum(len(d.get("meals", [])) for d in plan.get("days", []))},
    }


async def _get_shopping_list_db(user_id: str) -> dict | None:
    from sqlalchemy import select

    from app.database.models.saved_shopping import SavedShoppingItem, SavedShoppingList
    from app.database.session import get_session

    async with get_session() as session:
        result = await session.execute(
            select(SavedShoppingList).where(SavedShoppingList.user_id == user_id).order_by(SavedShoppingList.created_at.desc()).limit(1)
        )
        sl = result.scalar_one_or_none()
        if not sl:
            return None
        items_result = await session.execute(
            select(SavedShoppingItem).where(SavedShoppingItem.list_id == sl.id)
        )
        items = [
            {
                "id": row.id,
                "ingredient_name": row.ingredient_name,
                "total_quantity": row.total_quantity,
                "unit": row.unit,
                "estimated_cost": row.estimated_cost,
                "category": row.category,
                "already_have": row.already_have,
                "need": row.need,
                "purchased": row.purchased,
            }
            for row in items_result.scalars().all()
        ]
        return {
            "id": sl.id,
            "plan_id": sl.plan_id,
            "created_at": sl.created_at,
            "items": items,
        }


def _get_shopping_list_memory(user_id: str) -> dict | None:
    from app.data.stores import SHOPPING_ITEMS, SHOPPING_LISTS

    lists = SHOPPING_LISTS.get(user_id, [])
    if not lists:
        return None
    sl = lists[0]
    items = SHOPPING_ITEMS.get(sl["id"], [])
    return {**sl, "items": items}


@app.get("/api/shopping-list/{user_id}")
async def get_shopping_list(user_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        data = await _get_shopping_list_db(user_id)
    else:
        data = _get_shopping_list_memory(user_id)

    if not data:
        return {"success": False, "error": "No shopping list found. Apply a meal plan first."}

    total_cost = sum(it["estimated_cost"] for it in data["items"])
    return {"success": True, "shopping_list": data, "total_cost": round(total_cost, 2)}


async def _toggle_item_db(item_id: str) -> dict | None:
    from sqlalchemy import select, update

    from app.database.models.saved_shopping import SavedShoppingItem
    from app.database.session import get_session

    async with get_session() as session:
        result = await session.execute(select(SavedShoppingItem).where(SavedShoppingItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            return None
        new_val = not item.purchased
        stmt = update(SavedShoppingItem).where(SavedShoppingItem.id == item_id).values(purchased=new_val)
        await session.execute(stmt)
        await session.commit()
        return {"id": item_id, "purchased": new_val}


def _toggle_item_memory(item_id: str) -> dict | None:
    from app.data.stores import SHOPPING_ITEMS

    for list_id, items in SHOPPING_ITEMS.items():
        for item in items:
            if item["id"] == item_id:
                item["purchased"] = not item["purchased"]
                return {"id": item_id, "purchased": item["purchased"]}
    return None


@app.put("/api/shopping-list/{user_id}/toggle-item/{item_id}")
async def toggle_shopping_item(user_id: str, item_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        result = await _toggle_item_db(item_id)
    else:
        result = _toggle_item_memory(item_id)

    if not result:
        return {"success": False, "error": "Item not found"}
    return {"success": True, "item": result}


@app.post("/api/check-ai-quota")
async def check_ai_quota():
    if not is_ai_enabled():
        return {"available": False, "error": "AI is disabled (AI_ENABLED=false)"}

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return {"available": False, "error": "No API key configured. Add GOOGLE_API_KEY to .env"}

    models_to_try = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-3-flash-preview"]
    from google import genai

    client = genai.Client(api_key=api_key).aio
    last_error = ""

    for model in models_to_try:
        try:
            await client.models.generate_content(model=model, contents="ok")
            print(f"[Gemini] Quota check: {model} available")
            return {"available": True, "model": model, "error": ""}
        except Exception as e:
            err_str = str(e)
            last_error = err_str[:200]
            print(f"[Gemini] Quota check: {model} failed: {err_str[:100]}")

            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                print(f"[Gemini] Quota check: {model} exhausted")
                continue
            if "not found" in err_str.lower() or "not supported" in err_str.lower():
                continue
            if "API key" in err_str:
                return {"available": False, "error": f"Invalid API key: {err_str[:120]}"}
            if "permission" in err_str.lower() or "not enabled" in err_str.lower() or "access" in err_str.lower():
                return {"available": False, "error": f"API access denied: {err_str[:120]}"}

    return {
        "available": False,
        "error": f"AI generation failed. Last error: {last_error}",
    }


@app.post("/api/admin/reload-env")
async def reload_env(data: dict = {}):
    api_key = data.get("api_key", "")
    ai_enabled = data.get("ai_enabled")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    if ai_enabled is not None:
        set_ai_enabled(str(ai_enabled).lower() == "true")
        os.environ["AI_ENABLED"] = str(ai_enabled).lower()
        print(f"[Config] AI_ENABLED set to {is_ai_enabled()} via reload-env")
    _RECIPE_CACHE.clear()

    k = os.environ.get("GOOGLE_API_KEY", "")
    if not k:
        return {"success": False, "error": "No GOOGLE_API_KEY set in environment"}
    try:
        from google import genai
        client = genai.Client(api_key=k)
        client.models.count_tokens(model="gemini-2.5-flash-lite", contents="test")
        print(f"[Gemini] Key ...{k[-4:]} verified OK")
        return {"success": True, "error": "", "message": "Key verified OK"}
    except Exception as e:
        err_str = str(e)
        if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            msg = "Key valid but no remaining quota. Wait for reset or use a different project."
            print(f"[Gemini] {msg}")
            return {"success": False, "error": msg}
        elif "API key" in err_str:
            msg = f"Invalid API key: {err_str[:120]}"
            print(f"[Gemini] {msg}")
            return {"success": False, "error": msg}
        msg = f"Key check failed: {err_str[:200]}"
        print(f"[Gemini] {msg}")
        return {"success": False, "error": msg}


# ── Notification REST Endpoints ─────────────────────────────────────────



@app.get("/api/notifications/{user_id}")
async def get_notifications(user_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        from app.database.session import get_session
        from app.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            notifs = await service.get_for_user(user_id)
            unread = await service.unread_count(user_id)
            return {"success": True, "notifications": notifs, "unread_count": unread}

    from app.services.in_memory_notification import (
        get_for_user_in_memory,
        unread_count_in_memory,
    )

    notifs = get_for_user_in_memory(user_id)
    unread = unread_count_in_memory(user_id)
    return {"success": True, "notifications": notifs, "unread_count": unread}



@app.put("/api/notifications/{user_id}/read-all")
async def mark_all_notifications_read(user_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        from app.database.session import get_session
        from app.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            count = await service.mark_all_read(user_id)
            return {"success": True, "marked_read": count}

    from app.services.in_memory_notification import mark_all_read_in_memory

    count = mark_all_read_in_memory(user_id)
    return {"success": True, "marked_read": count}



@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        from app.database.session import get_session
        from app.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            ok = await service.mark_read(notification_id)
            return {"success": ok}

    from app.services.in_memory_notification import mark_read_in_memory

    ok = mark_read_in_memory(notification_id)
    return {"success": ok}



@app.get("/api/notifications/{user_id}/unread-count")
async def get_unread_count(user_id: str):
    from app.database.session import is_db_initialized

    if is_db_initialized():
        from app.database.session import get_session
        from app.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            count = await service.unread_count(user_id)
            return {"unread_count": count}

    from app.services.in_memory_notification import unread_count_in_memory

    return {"unread_count": unread_count_in_memory(user_id)}



# ── WebSocket ───────────────────────────────────────────────────────────


@app.websocket("/api/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    from app.websocket_manager import manager

    await websocket.accept()
    manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)



# ── Helper: emit notification + WS ─────────────────────────────────────


async def _emit_notification(user_id: str, type_: str, title: str, message: str) -> dict | None:
    from app.database.session import is_db_initialized
    from app.websocket_manager import manager

    notif = None
    if is_db_initialized():
        from app.database.session import get_session
        from app.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            notif = await service.create(user_id, type_, title, message)
    else:
        from app.services.in_memory_notification import create_in_memory

        notif = create_in_memory(user_id, type_, title, message)

    if notif:
        await manager.send(user_id, {"type": "notification", "notification": notif})

    return notif



# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
