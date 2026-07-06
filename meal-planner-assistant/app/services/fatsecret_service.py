"""FatSecret Platform API service (OAuth 2.0 Client Credentials)."""

import logging
import os
import time
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_FATSECRET_TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
_FATSECRET_API_URL = "https://platform.fatsecret.com/rest/server.api"

_token_cache: dict[str, Any] = {}


async def _get_access_token() -> str | None:
    client_id = os.environ.get("FATSECRET_CLIENT_ID") or os.environ.get("FATSECRET_CONSUMER_KEY", "")
    client_secret = os.environ.get("FATSECRET_CLIENT_SECRET") or os.environ.get("FATSECRET_CONSUMER_SECRET", "")

    if not client_id or not client_secret:
        logger.warning("[FatSecret] credentials not set")
        return None

    cached = _token_cache.get("token")
    expires_at = _token_cache.get("expires_at", 0)
    if cached and time.time() < expires_at - 60:
        return cached

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                _FATSECRET_TOKEN_URL,
                data={"grant_type": "client_credentials", "scope": "basic"},
                auth=aiohttp.BasicAuth(client_id, client_secret),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("[FatSecret] Token error %s: %s", resp.status, text[:200])
                    return None
                data = await resp.json()
                token = data.get("access_token")
                expires_in = data.get("expires_in", 86400)
                _token_cache["token"] = token
                _token_cache["expires_at"] = time.time() + expires_in
                logger.info("[FatSecret] Access token obtained, expires in %ss", expires_in)
                return token
    except Exception as e:
        logger.error("[FatSecret] Failed to get token: %s", e)
        return None


def _parse_nutrition_from_serving(serving: dict) -> dict:
    def safe_float(val: Any, default: float = 0.0) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    calories = safe_float(serving.get("calories", 0))
    protein = safe_float(serving.get("protein", 0))
    carbs = safe_float(serving.get("carbohydrate", 0))
    fat = safe_float(serving.get("fat", 0))
    metric_amount = safe_float(serving.get("metric_serving_amount", 100))
    metric_unit = (serving.get("metric_serving_unit") or "g").lower()

    if metric_amount > 0:
        factor = 100.0 / metric_amount
    else:
        factor = 1.0

    if metric_unit in ("ml", "milliliter", "millilitre"):
        factor = 100.0 / metric_amount if metric_amount > 0 else 1.0

    return {
        "calories_per_100g": round(calories * factor, 1),
        "protein_per_100g": round(protein * factor, 1),
        "carbs_per_100g": round(carbs * factor, 1),
        "fat_per_100g": round(fat * factor, 1),
    }


def _best_serving(servings_data: Any) -> dict | None:
    if not servings_data:
        return None

    serving = servings_data.get("serving")
    if not serving:
        return None

    if isinstance(serving, list):
        for s in serving:
            if s.get("metric_serving_amount"):
                return s
        return serving[0] if serving else None

    return serving


def _parse_nutrition_from_description(description: str) -> dict | None:
    import re

    if not description:
        return None

    def extract(pattern: str) -> float:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        return 0.0

    calories = extract(r"Calories:\s*([\d.]+)\s*kcal")
    fat = extract(r"Fat:\s*([\d.]+)\s*g")
    carbs = extract(r"Carbs:\s*([\d.]+)\s*g")
    protein = extract(r"Protein:\s*([\d.]+)\s*g")

    if calories == 0 and protein == 0 and carbs == 0 and fat == 0:
        return None

    return {
        "calories_per_100g": round(calories, 1),
        "protein_per_100g": round(protein, 1),
        "carbs_per_100g": round(carbs, 1),
        "fat_per_100g": round(fat, 1),
    }


async def search_foods(query: str, max_results: int = 8) -> list[dict]:
    if not query or not query.strip():
        return []

    token = await _get_access_token()
    if not token:
        return []

    params = {
        "method": "foods.search",
        "search_expression": query.strip(),
        "format": "json",
        "max_results": max_results,
        "page_number": 0,
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                _FATSECRET_API_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("[FatSecret] search error %s: %s", resp.status, text[:200])
                    return []
                data = await resp.json()
    except Exception as e:
        logger.error("[FatSecret] search request failed: %s", e)
        return []

    foods_data = data.get("foods", {})
    if not foods_data:
        return []

    food_list = foods_data.get("food", [])
    if isinstance(food_list, dict):
        food_list = [food_list]

    results = []
    for food in food_list:
        food_id = str(food.get("food_id", ""))
        food_name = food.get("food_name", "")
        brand_name = food.get("brand_name") or ""
        food_type = food.get("food_type", "Generic")
        nutrition = _parse_nutrition_from_description(food.get("food_description", ""))

        results.append({
            "food_id": food_id,
            "name": food_name,
            "brand": brand_name,
            "food_type": food_type,
            "nutrition": nutrition,
        })

    return results


async def get_food_by_id(food_id: str) -> dict | None:
    token = await _get_access_token()
    if not token:
        return None

    params = {
        "method": "food.get",
        "food_id": food_id,
        "format": "json",
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                _FATSECRET_API_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("[FatSecret] food.get error %s: %s", resp.status, text[:200])
                    return None
                data = await resp.json()
    except Exception as e:
        logger.error("[FatSecret] food.get request failed: %s", e)
        return None

    food = data.get("food")
    if not food:
        return None

    servings_data = food.get("servings")
    best = _best_serving(servings_data) if servings_data else None
    nutrition = _parse_nutrition_from_serving(best) if best else None

    return {
        "food_id": str(food.get("food_id", food_id)),
        "name": food.get("food_name", ""),
        "brand": food.get("brand_name") or "",
        "food_type": food.get("food_type", "Generic"),
        "category": food.get("food_category") or "",
        "nutrition": nutrition,
    }
