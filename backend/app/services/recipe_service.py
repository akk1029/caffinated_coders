import asyncio
import json
from collections import defaultdict
from typing import List

import httpx

from app.core.config import settings

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
TOP_N = 6


async def _redis():
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def _meal_ingredients(meal: dict) -> set[str]:
    ingredients = set()
    for i in range(1, 21):
        val = meal.get(f"strIngredient{i}", "") or ""
        val = val.strip()
        if val:
            ingredients.add(val.lower())
    return ingredients


async def _fetch_meals_for_ingredient(client: httpx.AsyncClient, ingredient: str) -> list[dict]:
    try:
        r = await client.get(f"{MEALDB_BASE}/filter.php", params={"i": ingredient})
        r.raise_for_status()
        return r.json().get("meals") or []
    except Exception:
        return []


async def _fetch_meal_detail(client: httpx.AsyncClient, meal_id: str) -> dict | None:
    try:
        r = await client.get(f"{MEALDB_BASE}/lookup.php", params={"i": meal_id})
        r.raise_for_status()
        meals = r.json().get("meals")
        return meals[0] if meals else None
    except Exception:
        return None


async def generate_recipes(
    ingredients: List[str],
    expiring: List[str] | None = None,
) -> List[dict]:
    expiring_set = {e.lower() for e in (expiring or [])}
    pantry = {i.lower() for i in ingredients}

    cache_key = "mealdb_recipes_v2:" + ",".join(sorted(pantry))
    r = await _redis()
    if r:
        cached = await r.get(cache_key)
        if cached:
            await r.aclose()
            return json.loads(cached)

    async with httpx.AsyncClient(timeout=10) as client:
        searches = await asyncio.gather(
            *[_fetch_meals_for_ingredient(client, ing) for ing in pantry]
        )

        # Expiring ingredients score 3x, others 1x
        meal_score: dict[str, int] = defaultdict(int)
        meal_stub: dict[str, dict] = {}
        for ing, meal_list in zip(pantry, searches):
            weight = 3 if ing in expiring_set else 1
            for meal in meal_list:
                mid = meal["idMeal"]
                meal_score[mid] += weight
                meal_stub[mid] = meal

        top_ids = sorted(meal_score, key=lambda m: meal_score[m], reverse=True)[:TOP_N * 2]

        details = await asyncio.gather(
            *[_fetch_meal_detail(client, mid) for mid in top_ids]
        )

    result = []
    for detail in details:
        if detail is None:
            continue
        meal_ings = _meal_ingredients(detail)

        # Count pantry matches (fuzzy: substring both ways)
        used_ings = {
            ing for ing in meal_ings
            if any(ing in p or p in ing for p in pantry)
        }
        missing_ings = meal_ings - used_ings
        expiring_used = [ing for ing in used_ings if any(ing in e or e in ing for e in expiring_set)]

        # Skip meals where we use fewer than 2 pantry items or missing far outnumbers used
        if len(used_ings) < 2 or len(missing_ings) > len(used_ings) + 4:
            continue

        result.append({
            "id": detail["idMeal"],
            "title": detail["strMeal"],
            "image": detail.get("strMealThumb", ""),
            "category": detail.get("strCategory", ""),
            "area": detail.get("strArea", ""),
            "instructions": detail.get("strInstructions", ""),
            "source": detail.get("strSource", ""),
            "youtube": detail.get("strYoutube", ""),
            "usedIngredientCount": len(used_ings),
            "missedIngredientCount": len(missing_ings),
            "expiringUsed": expiring_used,
            "ingredients": sorted(meal_ings),
            "usedIngredients": sorted(used_ings),
        })

    # Sort: expiring items used first, then most pantry items used
    result.sort(key=lambda x: (len(x["expiringUsed"]), x["usedIngredientCount"]), reverse=True)
    result = result[:TOP_N]

    if r:
        await r.setex(cache_key, 3600, json.dumps(result))
        await r.aclose()

    return result
