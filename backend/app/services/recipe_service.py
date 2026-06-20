import asyncio
import json
from collections import defaultdict
from typing import List

import httpx

from app.core.config import settings

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
TOP_N = 5


async def _redis():
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def _meal_ingredients(meal: dict) -> set[str]:
    """Extract non-empty ingredient names from a MealDB meal detail object."""
    ingredients = set()
    for i in range(1, 21):
        val = meal.get(f"strIngredient{i}", "") or ""
        val = val.strip()
        if val:
            ingredients.add(val.lower())
    return ingredients


async def _fetch_meals_for_ingredient(client: httpx.AsyncClient, ingredient: str) -> list[dict]:
    """Return list of {idMeal, strMeal, strMealThumb} for a single ingredient."""
    try:
        r = await client.get(f"{MEALDB_BASE}/filter.php", params={"i": ingredient})
        r.raise_for_status()
        data = r.json()
        return data.get("meals") or []
    except Exception:
        return []


async def _fetch_meal_detail(client: httpx.AsyncClient, meal_id: str) -> dict | None:
    try:
        r = await client.get(f"{MEALDB_BASE}/lookup.php", params={"i": meal_id})
        r.raise_for_status()
        data = r.json()
        meals = data.get("meals")
        return meals[0] if meals else None
    except Exception:
        return None


async def generate_recipes(ingredients: List[str]) -> List[dict]:
    cache_key = "mealdb_recipes:" + ",".join(sorted(i.lower() for i in ingredients))

    r = await _redis()
    if r:
        cached = await r.get(cache_key)
        if cached:
            await r.aclose()
            return json.loads(cached)

    pantry = {i.lower() for i in ingredients}

    async with httpx.AsyncClient(timeout=10) as client:
        # Query TheMealDB for each pantry ingredient in parallel
        searches = await asyncio.gather(
            *[_fetch_meals_for_ingredient(client, ing) for ing in pantry]
        )

        # Score each meal by how many pantry ingredients it appears under
        meal_score: dict[str, int] = defaultdict(int)
        meal_stub: dict[str, dict] = {}
        for meal_list in searches:
            for meal in meal_list:
                mid = meal["idMeal"]
                meal_score[mid] += 1
                meal_stub[mid] = meal

        # Take top N by score
        top_ids = sorted(meal_score, key=lambda m: meal_score[m], reverse=True)[:TOP_N]

        # Fetch full details in parallel
        details = await asyncio.gather(
            *[_fetch_meal_detail(client, mid) for mid in top_ids]
        )

    result = []
    for detail in details:
        if detail is None:
            continue
        meal_ings = _meal_ingredients(detail)
        used = len(pantry & meal_ings)
        missing = len(meal_ings - pantry)
        result.append({
            "id": detail["idMeal"],
            "title": detail["strMeal"],
            "image": detail.get("strMealThumb", ""),
            "category": detail.get("strCategory", ""),
            "area": detail.get("strArea", ""),
            "instructions": detail.get("strInstructions", ""),
            "source": detail.get("strSource", ""),
            "youtube": detail.get("strYoutube", ""),
            "usedIngredientCount": used,
            "missedIngredientCount": missing,
        })

    # Sort by most pantry ingredients used
    result.sort(key=lambda x: x["usedIngredientCount"], reverse=True)

    if r:
        await r.setex(cache_key, 86400, json.dumps(result))
        await r.aclose()

    return result
