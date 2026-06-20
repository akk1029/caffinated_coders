"""
Receipt scanner (English receipts): Google Vision OCR -> parse line items
(name, qty, unit, RM price) -> shelf life from food_data.

Falls back to a mock result when the API key is missing or the call fails,
so the feature still works offline/demo.
"""
import base64
import logging
import re
from datetime import date
from typing import Dict, List

import httpx

from app.core.config import settings
from app.services.food_data import shelf_days, estimate_cost, SHELF_LIFE

logger = logging.getLogger("pantrypet.receipt")

VISION_URL = "https://vision.googleapis.com/v1/images:annotate"
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

# ── Malay (and a few common) grocery terms -> canonical English food name ──
MALAY_TO_EN = {
    "ayam": "chicken", "daging lembu": "beef", "lembu": "beef", "daging": "beef",
    "babi": "pork", "kambing": "lamb", "ikan": "fish", "udang": "prawn",
    "sotong": "squid", "ketam": "crab",
    "telur": "egg", "susu": "milk", "beras": "rice", "nasi": "rice",
    "roti": "bread", "keju": "cheese", "mentega": "butter", "marjerin": "butter",
    "minyak": "oil", "gula": "sugar", "garam": "salt", "tepung": "flour",
    "bawang putih": "garlic", "bawang": "onion",
    "tomato": "tomato", "kentang": "potato", "lobak merah": "carrot", "lobak": "carrot",
    "sayur": "vegetable", "epal": "apple", "pisang": "banana", "limau": "lime",
    "oren": "orange", "tembikai": "watermelon", "nanas": "pineapple", "mangga": "mango",
    "anggur": "grape", "strawberi": "strawberry", "betik": "papaya",
    "cendawan": "mushroom", "timun": "cucumber", "bayam": "spinach",
    "brokoli": "broccoli", "kubis": "cabbage", "salad": "lettuce", "cili": "pepper",
    "halia": "ginger", "sosej": "hot dog", "yogurt": "yogurt", "jagung": "corn",
    "tauhu": "tofu", "taufu": "tofu", "mi": "pasta", "pasta": "pasta",
}

# English food keywords come from food_data plus the Malay map (token -> English)
TOKEN_TO_EN = {**{k: k for k in SHELF_LIFE}, **MALAY_TO_EN}


async def _redis():
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


# ── Daily scan quota (per user, stored in Redis) ──────────────────────────────

def _quota_key(user_id: str) -> str:
    return f"receipt_scans:{user_id}:{date.today().isoformat()}"


async def get_scan_count(user_id: str) -> int:
    r = await _redis()
    if not r:
        return 0
    v = await r.get(_quota_key(user_id))
    await r.aclose()
    return int(v) if v else 0


async def incr_scan_count(user_id: str) -> int:
    r = await _redis()
    if not r:
        return 0
    key = _quota_key(user_id)
    v = await r.incr(key)
    if v == 1:
        await r.expire(key, 172800)  # auto-clean after 2 days
    await r.aclose()
    return v


# ── OCR + translation ─────────────────────────────────────────────────────────

async def _ocr(image_bytes: bytes) -> str:
    """Full-text OCR. Prefers Google Vision (needs GCP billing); otherwise uses the
    FREE OCR.space API (no billing/credit card) when OCR_SPACE_API_KEY is set."""
    if settings.GOOGLE_API_KEY:
        return await _ocr_google(image_bytes)
    if settings.OCR_SPACE_API_KEY:
        return await _ocr_ocrspace(image_bytes)
    raise RuntimeError("No OCR provider configured")


async def _ocr_google(image_bytes: bytes) -> str:
    payload = {
        "requests": [{
            "image": {"content": base64.b64encode(image_bytes).decode()},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
        }]
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(VISION_URL, params={"key": settings.GOOGLE_API_KEY}, json=payload)
        r.raise_for_status()
        resp = r.json()["responses"][0]
    if "error" in resp:
        raise RuntimeError(resp["error"].get("message", "Vision API error"))
    return resp.get("fullTextAnnotation", {}).get("text", "")


async def _ocr_ocrspace(image_bytes: bytes) -> str:
    """Free OCR via OCR.space — no billing. Free tier limit is ~1 MB per image."""
    data = {
        "apikey": settings.OCR_SPACE_API_KEY,
        "base64Image": "data:image/png;base64," + base64.b64encode(image_bytes).decode(),
        "language": "eng",
        "OCREngine": "2",
        "isTable": "true",
        "scale": "true",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(OCR_SPACE_URL, data=data)
        r.raise_for_status()
        j = r.json()
    if j.get("IsErroredOnProcessing"):
        err = j.get("ErrorMessage")
        msg = err[0] if isinstance(err, list) and err else (err or "OCR.space error")
        raise RuntimeError(str(msg))
    return "\n".join(p.get("ParsedText", "") for p in (j.get("ParsedResults") or []))


# ── Parsing ──────────────────────────────────────────────────────────────────

def _match_food(line_lower: str):
    best, best_len = None, -1
    for token, en in TOKEN_TO_EN.items():
        if token in line_lower and len(token) > best_len:
            best, best_len = en, len(token)
    return best


def _norm_unit(u: str) -> str:
    u = u.lower()
    if u == "kg":
        return "kg"
    if u in ("g", "gram", "gm"):
        return "g"
    if u in ("l", "liter", "litre"):
        return "liters"
    if u == "ml":
        return "ml"
    return "pieces"


def _parse(text: str) -> List[Dict]:
    items, seen = [], set()
    for raw in text.splitlines():
        low = raw.strip().lower()
        if not low:
            continue
        en = _match_food(low)
        if not en or en in seen:
            continue

        prices = re.findall(r"(?:rm)?\s*(\d{1,4}[.,]\d{2})", low)
        price = float(prices[-1].replace(",", ".")) if prices else None

        qty, unit = 1.0, "pieces"
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|gram|gm|g|ml|litre|liter|l|pcs|pkt|biji|btl|unit)\b", low)
        if m:
            qty = float(m.group(1).replace(",", "."))
            unit = _norm_unit(m.group(2))

        cost = price if price is not None else estimate_cost(en, qty, unit)
        items.append({
            "item_name": en.title(),
            "quantity": qty,
            "unit": unit,
            "suggested_shelf_days": shelf_days(en),
            "estimated_cost": round(cost, 2),
        })
        seen.add(en)
    return items


async def scan_receipt(image_bytes: bytes) -> Dict:
    """Returns {items, demo, error}. Auto-adding is done by the router."""
    if not (settings.GOOGLE_API_KEY or settings.OCR_SPACE_API_KEY):
        msg = "Receipt OCR not configured: set GOOGLE_API_KEY or OCR_SPACE_API_KEY."
        logger.warning(msg)
        return {"items": [], "demo": True, "error": msg}
    try:
        text = await _ocr(image_bytes)
        return {"items": _parse(text), "demo": False, "error": None}
    except httpx.HTTPStatusError as e:
        body = e.response.text[:300]
        logger.error("Receipt OCR HTTP failed (%s): %s", e.response.status_code, body)
        return {"items": [], "demo": True, "error": f"OCR API HTTP {e.response.status_code}: {body}"}
    except Exception as e:
        logger.exception("Receipt OCR failed")
        return {"items": [], "demo": True, "error": f"{type(e).__name__}: {e}"}


def _mock_items() -> List[Dict]:
    samples = [("Chicken", 1, "kg"), ("Milk", 2, "liters"), ("Eggs", 10, "pieces"), ("Rice", 1, "kg")]
    return [
        {
            "item_name": n,
            "quantity": q,
            "unit": u,
            "suggested_shelf_days": shelf_days(n),
            "estimated_cost": estimate_cost(n, q, u),
        }
        for n, q, u in samples
    ]
