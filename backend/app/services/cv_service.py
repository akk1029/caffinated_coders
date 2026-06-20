import base64
import logging
from typing import Dict, List

import httpx

from app.core.config import settings

logger = logging.getLogger("pantrypet.cv")

VISION_URL = "https://vision.googleapis.com/v1/images:annotate"

SHELF_LIFE_DEFAULTS: Dict[str, int] = {
    "apple": 14, "banana": 7, "orange": 21, "grape": 7, "strawberry": 5,
    "mango": 7, "pineapple": 5, "lemon": 21, "lime": 21, "avocado": 5,
    "carrot": 21, "broccoli": 7, "spinach": 5, "tomato": 10, "potato": 30,
    "onion": 30, "garlic": 60, "ginger": 14, "cabbage": 14, "lettuce": 7,
    "cucumber": 10, "pepper": 14, "celery": 14, "mushroom": 7, "corn": 5,
    "chicken": 3, "beef": 3, "pork": 3, "fish": 2, "salmon": 2, "tuna": 2,
    "egg": 21, "milk": 7, "cheese": 14, "butter": 30, "yogurt": 14,
    "bread": 7, "rice": 365, "pasta": 365,
}

FOOD_OBJECTS = set(SHELF_LIFE_DEFAULTS.keys()) | {
    "food", "fruit", "vegetable", "produce", "meat", "dairy", "grain",
    "seafood", "poultry", "citrus", "berry", "herb", "spice",
}


async def detect_ingredients(image_bytes: bytes) -> Dict:
    """Detect food items in an image via the Google Vision REST API (API-key auth).

    Returns {"items": [...], "demo": bool, "error": str | None}.
    demo=True means the items are placeholder samples (NOT real detection).
    """
    if not settings.GOOGLE_API_KEY:
        msg = "Google Vision not configured: GOOGLE_API_KEY is empty. Returning DEMO data, not real detection."
        logger.warning(msg)
        return {"items": _mock_result(), "demo": True, "error": msg}

    try:
        payload = {
            "requests": [{
                "image": {"content": base64.b64encode(image_bytes).decode()},
                "features": [
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 20},
                    {"type": "LABEL_DETECTION", "maxResults": 20},
                ],
            }]
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(VISION_URL, params={"key": settings.GOOGLE_API_KEY}, json=payload)
            r.raise_for_status()
            resp = r.json()["responses"][0]

        if "error" in resp:
            raise RuntimeError(resp["error"].get("message", "Vision API error"))

        seen: Dict[str, float] = {}
        for obj in resp.get("localizedObjectAnnotations", []):
            name = obj["name"].lower().strip()
            root = name.split()[0]
            score = obj.get("score", 0)
            if any(food in name for food in FOOD_OBJECTS):
                if root not in seen or seen[root] < score:
                    seen[root] = score
        for label in resp.get("labelAnnotations", []):
            name = label["description"].lower().strip()
            score = label.get("score", 0)
            if name in FOOD_OBJECTS and name not in seen and score > 0.65:
                seen[name] = score

        items = [
            {
                "item_name": name.title(),
                "suggested_shelf_days": SHELF_LIFE_DEFAULTS.get(name, 7),
                "confidence": round(score, 2),
            }
            for name, score in seen.items()
        ]
        if not items:
            logger.info("Vision succeeded but recognised no food items in this image.")
            return {"items": [], "demo": False, "error": "No food items recognised in the photo."}

        logger.info("Vision detected %d food item(s): %s", len(items), [i["item_name"] for i in items])
        return {"items": items, "demo": False, "error": None}

    except httpx.HTTPStatusError as e:
        # Surface API errors (bad key, API not enabled, quota) clearly.
        body = e.response.text[:300]
        logger.error("Vision REST call failed (%s): %s", e.response.status_code, body)
        return {"items": _mock_result(), "demo": True, "error": f"Vision API HTTP {e.response.status_code}: {body}"}
    except Exception as e:
        logger.exception("Google Vision detection failed")
        return {"items": _mock_result(), "demo": True, "error": f"{type(e).__name__}: {e}"}


def _mock_result() -> List[Dict]:
    return [
        {"item_name": "Apple", "suggested_shelf_days": 14, "confidence": 0.92},
        {"item_name": "Carrot", "suggested_shelf_days": 21, "confidence": 0.87},
        {"item_name": "Onion", "suggested_shelf_days": 30, "confidence": 0.81},
    ]
