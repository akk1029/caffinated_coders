"""
Reference food data used to auto-fill shelf life, estimated cost (RM) and CO2.

Shelf-life ranges follow the FoodSafety.gov Cold Food Storage Chart where
available, with broader pantry items added for coverage. Prices are typical
Malaysian retail (RM per kg). CO2 factors are kg CO2e per kg of food
(Poore & Nemecek, 2018 / Our World in Data).
"""
from typing import Optional, Tuple

# ── Shelf life: keyword -> (min_days, max_days). min is used as the expiry. ──
SHELF_LIFE = {
    # FoodSafety.gov Cold Food Storage Chart
    "egg": (21, 35),
    "hot dog": (7, 7),
    "ground": (1, 2), "mince": (1, 2), "hamburger": (1, 2),
    "chicken": (1, 2), "turkey": (1, 2), "poultry": (1, 2),
    "leftover": (3, 4),
    "pizza": (3, 4),
    "rice": (365, 730),
    "milk": (7, 7),
    "spinach": (3, 5),
    "apple": (14, 21),
    # Broader pantry coverage
    "banana": (5, 7), "orange": (14, 21), "grape": (5, 7), "strawberry": (3, 5),
    "mango": (5, 7), "pineapple": (4, 5), "lemon": (14, 21), "lime": (14, 21),
    "avocado": (3, 5), "carrot": (21, 28), "broccoli": (5, 7), "tomato": (7, 10),
    "potato": (30, 60), "onion": (30, 60), "garlic": (60, 90), "ginger": (14, 21),
    "cabbage": (14, 21), "lettuce": (5, 7), "cucumber": (7, 10), "pepper": (10, 14),
    "celery": (10, 14), "mushroom": (5, 7), "corn": (3, 5),
    "beef": (3, 5), "pork": (3, 5), "fish": (1, 2), "salmon": (1, 2), "tuna": (1, 2),
    "cheese": (14, 21), "butter": (30, 60), "yogurt": (10, 14),
    "bread": (5, 7), "pasta": (365, 730), "flour": (365, 365), "sugar": (730, 730),
    "honey": (730, 730), "oil": (365, 365),
}
DEFAULT_SHELF = (7, 7)

# ── Price: keyword -> RM per kg (typical Malaysian retail) ──
PRICE_PER_KG_RM = {
    "beef": 35, "lamb": 45, "pork": 22, "chicken": 13, "turkey": 18,
    "fish": 25, "salmon": 50, "tuna": 30, "prawn": 40, "shrimp": 40,
    "egg": 12, "milk": 7, "cheese": 35, "butter": 25, "yogurt": 12,
    "rice": 5, "pasta": 8, "bread": 8, "flour": 4, "sugar": 4, "oil": 9, "honey": 30,
    "apple": 9, "banana": 5, "orange": 8, "grape": 18, "strawberry": 30, "mango": 10,
    "pineapple": 4, "lemon": 10, "lime": 10, "avocado": 20,
    "carrot": 4, "broccoli": 9, "spinach": 8, "tomato": 6, "potato": 4, "onion": 4,
    "garlic": 12, "ginger": 10, "cabbage": 3, "lettuce": 7, "cucumber": 4,
    "pepper": 10, "celery": 8, "mushroom": 16, "corn": 5,
    "hot dog": 18, "pizza": 20, "leftover": 15,
}
DEFAULT_PRICE_PER_KG = 12.0

# ── CO2: keyword -> kg CO2e per kg food ──
CO2_FACTORS = {
    "beef": 27.0, "lamb": 24.0, "cheese": 21.0, "pork": 7.0, "chicken": 6.0,
    "turkey": 6.0, "fish": 5.0, "salmon": 6.0, "tuna": 6.0, "prawn": 12.0, "shrimp": 12.0,
    "egg": 4.5, "rice": 4.0, "milk": 3.0, "yogurt": 3.0, "butter": 12.0,
    "bread": 1.3, "pasta": 1.2, "flour": 1.1, "sugar": 1.8, "oil": 3.0, "honey": 2.0,
    "apple": 0.4, "banana": 0.7, "orange": 0.4, "grape": 0.7, "strawberry": 0.4,
    "tomato": 1.4, "potato": 0.5, "onion": 0.4, "carrot": 0.4, "broccoli": 0.5,
    "spinach": 0.5, "lettuce": 0.5, "cucumber": 0.6, "cabbage": 0.4, "mushroom": 1.0,
    "hot dog": 7.0, "pizza": 4.0, "leftover": 4.0,
}
DEFAULT_CO2 = 2.5

# ── Average weight per piece (kg) for count-based units ──
PIECE_KG = {
    "egg": 0.05, "apple": 0.18, "banana": 0.12, "orange": 0.18, "lemon": 0.10,
    "lime": 0.07, "potato": 0.17, "onion": 0.15, "tomato": 0.12, "avocado": 0.20,
    "carrot": 0.07, "mango": 0.30, "hot dog": 0.05, "pizza": 0.30,
}
DEFAULT_PIECE_KG = 0.15


def _match(name: str, table: dict):
    """Return the value for the longest keyword found in name, else None."""
    n = (name or "").lower()
    best, best_len = None, -1
    for kw, val in table.items():
        if kw in n and len(kw) > best_len:
            best, best_len = val, len(kw)
    return best


def to_kg(quantity, unit: str, name: str = "") -> float:
    """Best-effort conversion of a quantity+unit to kilograms."""
    q = float(quantity or 0)
    u = (unit or "").lower().strip()
    if u in ("kg", "kilogram", "kilograms"):
        return q
    if u in ("g", "gram", "grams"):
        return q / 1000
    if u in ("l", "liter", "liters", "litre", "litres"):
        return q                      # ~1 kg per litre
    if u in ("ml", "milliliter", "milliliters"):
        return q / 1000
    if u in ("cup", "cups"):
        return q * 0.24
    if u in ("tbsp",):
        return q * 0.015
    if u in ("tsp",):
        return q * 0.005
    # pieces / count
    per = _match(name, PIECE_KG)
    return q * (per if per is not None else DEFAULT_PIECE_KG)


def shelf_range(name: str) -> Tuple[int, int]:
    return _match(name, SHELF_LIFE) or DEFAULT_SHELF


def shelf_days(name: str) -> int:
    """Conservative shelf life (min of the range) used to set expiry."""
    return shelf_range(name)[0]


def estimate_cost(name: str, quantity, unit: str) -> float:
    """Estimated retail value in RM for the given quantity."""
    price = _match(name, PRICE_PER_KG_RM)
    price = price if price is not None else DEFAULT_PRICE_PER_KG
    return round(max(to_kg(quantity, unit, name), 0.0) * price, 2)


def estimate_co2(name: str, quantity, unit: str) -> float:
    """Estimated CO2e (kg) prevented by using this item instead of wasting it."""
    factor = _match(name, CO2_FACTORS)
    factor = factor if factor is not None else DEFAULT_CO2
    return round(max(to_kg(quantity, unit, name), 0.0) * factor, 4)
