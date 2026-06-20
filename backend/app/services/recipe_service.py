import httpx
import json
from typing import List
from app.core.config import settings


async def _redis():
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


async def generate_recipes(ingredients: List[str]) -> List[dict]:
    """
    Fetch recipes from Spoonacular. Caches results in Redis for 24 h so
    identical ingredient sets don't burn API quota.
    """
    cache_key = "recipes:" + ",".join(sorted(i.lower() for i in ingredients))

    r = await _redis()
    if r:
        cached = await r.get(cache_key)
        if cached:
            return json.loads(cached)

    if not settings.SPOONACULAR_API_KEY:
        result = _mock_recipes(ingredients)
    else:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.spoonacular.com/recipes/findByIngredients",
                params={
                    "ingredients": ",".join(ingredients),
                    "number": 5,
                    "ranking": 2,
                    "ignorePantry": True,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
            )
            response.raise_for_status()
            result = response.json()

    if r:
        await r.setex(cache_key, 86400, json.dumps(result))
        await r.aclose()

    return result


def _mock_recipes(ingredients: List[str]) -> List[dict]:
    primary = ingredients[0].title() if ingredients else "Pantry"
    return [
        {
            "id": 1,
            "title": f"{primary} Stir Fry",
            "usedIngredientCount": min(3, len(ingredients)),
            "missedIngredientCount": 1,
            "image": "https://placehold.co/300x200/4caf50/white?text=Recipe",
        },
        {
            "id": 2,
            "title": f"Roasted {primary} Bowl",
            "usedIngredientCount": min(2, len(ingredients)),
            "missedIngredientCount": 2,
            "image": "https://placehold.co/300x200/ff9800/white?text=Recipe",
        },
    ]
