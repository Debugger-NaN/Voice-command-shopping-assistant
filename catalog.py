"""
catalog.py
Static domain knowledge used for categorization, seasonal suggestions,
substitute suggestions, and the mock product catalog used for voice search.

This is intentionally a plain-Python data module (no external DB, no paid
APIs) so the whole assistant runs on a free tier with zero setup.
"""

from datetime import datetime

# ---------------------------------------------------------------------------
# 1. Item -> category map, used to auto-categorize whatever the user adds.
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "milk": "Dairy", "cheese": "Dairy", "yogurt": "Dairy", "butter": "Dairy",
    "curd": "Dairy", "paneer": "Dairy", "almond milk": "Dairy",
    "soy milk": "Dairy", "cream": "Dairy",

    "apple": "Produce", "apples": "Produce", "banana": "Produce",
    "bananas": "Produce", "orange": "Produce", "oranges": "Produce",
    "tomato": "Produce", "tomatoes": "Produce", "onion": "Produce",
    "onions": "Produce", "potato": "Produce", "potatoes": "Produce",
    "spinach": "Produce", "carrot": "Produce", "carrots": "Produce",
    "grapes": "Produce", "mango": "Produce", "mangoes": "Produce",
    "lettuce": "Produce", "cucumber": "Produce", "garlic": "Produce",

    "bread": "Bakery", "bun": "Bakery", "buns": "Bakery", "bagel": "Bakery",
    "croissant": "Bakery",

    "chicken": "Meat & Seafood", "eggs": "Meat & Seafood", "egg": "Meat & Seafood",
    "fish": "Meat & Seafood", "shrimp": "Meat & Seafood", "mutton": "Meat & Seafood",

    "chips": "Snacks", "cookies": "Snacks", "biscuits": "Snacks",
    "chocolate": "Snacks", "namkeen": "Snacks", "popcorn": "Snacks",

    "water": "Beverages", "juice": "Beverages", "soda": "Beverages",
    "coffee": "Beverages", "tea": "Beverages",

    "rice": "Pantry", "flour": "Pantry", "sugar": "Pantry", "salt": "Pantry",
    "oil": "Pantry", "pasta": "Pantry", "lentils": "Pantry", "dal": "Pantry",
    "toothpaste": "Household", "soap": "Household", "shampoo": "Household",
    "detergent": "Household", "tissue": "Household", "tissues": "Household",
}

DEFAULT_CATEGORY = "Other"


def categorize(item_name: str) -> str:
    key = item_name.lower().strip()
    if key in CATEGORY_MAP:
        return CATEGORY_MAP[key]
    # try partial match (e.g. "organic apples" -> "apples")
    for known, cat in CATEGORY_MAP.items():
        if known in key or key in known:
            return cat
    return DEFAULT_CATEGORY


# ---------------------------------------------------------------------------
# 2. Seasonal recommendations by month (Northern-hemisphere-leaning, simple
#    illustrative table -- easy to extend/replace with a real API later).
# ---------------------------------------------------------------------------
SEASONAL_BY_MONTH = {
    1: ["oranges", "spinach", "carrots"],
    2: ["oranges", "cauliflower", "peas"],
    3: ["strawberries", "spinach", "peas"],
    4: ["mangoes", "strawberries", "asparagus"],
    5: ["mangoes", "watermelon", "cucumber"],
    6: ["watermelon", "mangoes", "corn"],
    7: ["watermelon", "corn", "tomatoes"],
    8: ["grapes", "corn", "tomatoes"],
    9: ["grapes", "apples", "pumpkin"],
    10: ["apples", "pumpkin", "sweet potato"],
    11: ["apples", "sweet potato", "cranberries"],
    12: ["oranges", "cranberries", "pomegranate"],
}


def seasonal_suggestions():
    month = datetime.now().month
    return SEASONAL_BY_MONTH.get(month, [])


# ---------------------------------------------------------------------------
# 3. Substitute suggestions.
# ---------------------------------------------------------------------------
SUBSTITUTES = {
    "milk": ["almond milk", "soy milk", "oat milk"],
    "butter": ["margarine", "olive oil"],
    "sugar": ["honey", "jaggery", "stevia"],
    "rice": ["quinoa", "cauliflower rice"],
    "bread": ["tortillas", "pita bread"],
    "pasta": ["zucchini noodles", "rice noodles"],
    "chicken": ["tofu", "paneer", "mushrooms"],
}


def get_substitutes(item_name: str):
    return SUBSTITUTES.get(item_name.lower().strip(), [])


# ---------------------------------------------------------------------------
# 4. Mock product catalog for voice-activated search (brand / price / size).
#    In production this would be a real product database or partner API.
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    {"name": "apples", "brand": "organic valley", "size": "1kg", "price": 3.50, "organic": True},
    {"name": "apples", "brand": "local farm", "size": "1kg", "price": 2.20, "organic": False},
    {"name": "milk", "brand": "amul", "size": "1L", "price": 1.80, "organic": False},
    {"name": "milk", "brand": "organic valley", "size": "1L", "price": 3.10, "organic": True},
    {"name": "toothpaste", "brand": "colgate", "size": "150g", "price": 2.99, "organic": False},
    {"name": "toothpaste", "brand": "sensodyne", "size": "100g", "price": 4.50, "organic": False},
    {"name": "bread", "brand": "britannia", "size": "400g", "price": 1.50, "organic": False},
    {"name": "bread", "brand": "harvest gold", "size": "400g", "price": 1.60, "organic": False},
    {"name": "rice", "brand": "india gate", "size": "5kg", "price": 8.00, "organic": False},
    {"name": "eggs", "brand": "farm fresh", "size": "12 pack", "price": 2.75, "organic": False},
]


def search_products(query: str, max_price: float | None = None, brand: str | None = None):
    query = (query or "").lower().strip()
    results = []
    for p in PRODUCT_CATALOG:
        if query and query not in p["name"] and p["name"] not in query:
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if brand and brand.lower() not in p["brand"].lower():
            continue
        results.append(p)
    return results
