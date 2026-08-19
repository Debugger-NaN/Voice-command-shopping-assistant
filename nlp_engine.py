"""
nlp_engine.py
A lightweight, dependency-free NLP layer that turns a raw voice transcript
into a structured intent: {action, item, quantity, unit, max_price, brand}.

Why regex/keyword-based instead of a heavy NLP library or a paid LLM API?
- Runs instantly on any free tier host with no extra memory footprint.
- Fully transparent / easy to extend with new phrasings.
- The assignment scopes this to "flexible phrasing", not open-domain
  understanding, so a well-designed pattern set covers the required cases
  ("Add milk", "I need apples", "I want to buy bananas", etc).

Multilingual support: keyword sets are provided for a few languages
(English, Spanish, Hindi-transliterated, French) so the same intents can be
recognized regardless of which language the browser's speech recognizer
returns. This is a deliberately lightweight approach -- see README for the
production alternative (a translation API) that a paid tier would use.
"""

import re

# ---------------------------------------------------------------------------
# Multilingual trigger phrases per intent. All matching is done on the
# lower-cased transcript.
# ---------------------------------------------------------------------------
ADD_TRIGGERS = [
    # English
    "add", "i need", "i want to buy", "i want", "buy", "get me", "put",
    "include",
    # Spanish
    "agregar", "añadir", "necesito", "quiero comprar", "comprar",
    # Hindi (transliterated)
    "jodo", "chahiye", "khareedo", "add karo",
    # French
    "ajouter", "j'ai besoin de", "acheter",
]

REMOVE_TRIGGERS = [
    "remove", "delete", "take off", "cancel", "get rid of",
    "quitar", "eliminar", "borrar",
    "hatao", "nikaalo",
    "supprimer", "enlever",
]

SEARCH_TRIGGERS = [
    "find", "search", "look for", "show me", "find me",
    "buscar", "encontrar",
    "dhundo", "khojo",
    "chercher", "trouver",
]

# Units recognized when extracting a quantity, e.g. "2 bottles of water"
UNITS = [
    "bottles?", "kgs?", "kilograms?", "grams?", "dozen", "pieces?", "pcs",
    "liters?", "litres?", "packs?", "packets?", "cans?", "boxes?", "bags?",
]
UNIT_PATTERN = "|".join(UNITS)

QUANTITY_RE = re.compile(
    rf"(\d+)\s*(?:({UNIT_PATTERN})\s*(?:of)?)?\s*(.+)", re.IGNORECASE
)

# Spoken number words -> digits, so "add two bottles of water" works just
# like "add 2 bottles of water" (speech recognizers usually return words
# for small numbers).
WORD_NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "dozen": 12,
}

WORD_NUMBER_RE = re.compile(
    r"^(" + "|".join(sorted(WORD_NUMBERS, key=len, reverse=True)) + r")\b\s*",
    re.IGNORECASE,
)


def _normalize_leading_number(text: str) -> str:
    """Convert a leading spoken number word to digits, e.g. 'two bottles' -> '2 bottles'."""
    match = WORD_NUMBER_RE.match(text)
    if match:
        word = match.group(1).lower()
        digit = WORD_NUMBERS[word]
        return f"{digit} {text[match.end():]}"
    return text

PRICE_RE = re.compile(r"under\s*\$?(\d+(?:\.\d+)?)|less than\s*\$?(\d+(?:\.\d+)?)", re.IGNORECASE)

# Common brand names to detect in a search query (extend as needed)
KNOWN_BRANDS = ["organic valley", "amul", "colgate", "sensodyne", "britannia",
                "harvest gold", "india gate", "farm fresh", "local farm"]


def _strip_trigger(text: str, trigger: str) -> str:
    """Remove a leading trigger phrase and tidy the remainder."""
    pattern = re.compile(rf"^\s*{re.escape(trigger)}\b[:,]?\s*", re.IGNORECASE)
    return pattern.sub("", text).strip()


def _find_trigger(text: str, triggers: list[str]):
    text_l = text.lower()
    # prefer the longest matching trigger so "i want to buy" beats "i want"
    matches = [t for t in triggers if text_l.startswith(t) or f" {t} " in f" {text_l} "]
    if not matches:
        return None
    return max(matches, key=len)


def _clean_tail(text: str) -> str:
    text = re.sub(r"\bfrom my list\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bto my list\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .,!")
    return text


def parse_command(raw_text: str) -> dict:
    """
    Parse a raw transcript into a structured intent.
    Returns a dict: {action, item, quantity, unit, max_price, brand, raw}
    action is one of: 'add', 'remove', 'search', 'unknown'
    """
    text = (raw_text or "").strip()
    result = {
        "action": "unknown",
        "item": None,
        "quantity": 1,
        "unit": None,
        "max_price": None,
        "brand": None,
        "raw": raw_text,
    }
    if not text:
        return result

    # --- price filter (checked first, doesn't change action detection) ---
    price_match = PRICE_RE.search(text)
    if price_match:
        result["max_price"] = float(price_match.group(1) or price_match.group(2))
        text = PRICE_RE.sub("", text).strip()

    # --- brand detection ---
    text_l = text.lower()
    for brand in KNOWN_BRANDS:
        if brand in text_l:
            result["brand"] = brand
            break

    # --- intent detection, longest trigger phrase wins ---
    remove_trigger = _find_trigger(text, REMOVE_TRIGGERS)
    add_trigger = _find_trigger(text, ADD_TRIGGERS)
    search_trigger = _find_trigger(text, SEARCH_TRIGGERS)

    if remove_trigger:
        result["action"] = "remove"
        tail = _strip_trigger(text, remove_trigger)
        result["item"] = _clean_tail(tail)
    elif search_trigger:
        result["action"] = "search"
        tail = _strip_trigger(text, search_trigger)
        result["item"] = _clean_tail(tail)
    elif add_trigger:
        result["action"] = "add"
        tail = _strip_trigger(text, add_trigger)
        tail = _clean_tail(_normalize_leading_number(tail))
        qty_match = QUANTITY_RE.match(tail)
        if qty_match:
            result["quantity"] = int(qty_match.group(1))
            result["unit"] = qty_match.group(2)
            result["item"] = qty_match.group(3).strip()
        else:
            result["item"] = tail
    else:
        # No explicit trigger -- fall back to treating the whole
        # utterance as an "add" of that item (common short form: "milk").
        tail = _clean_tail(_normalize_leading_number(text))
        qty_match = QUANTITY_RE.match(tail)
        if qty_match and qty_match.group(2):
            result["action"] = "add"
            result["quantity"] = int(qty_match.group(1))
            result["unit"] = qty_match.group(2)
            result["item"] = qty_match.group(3).strip()
        elif tail:
            result["action"] = "add"
            result["item"] = tail

    if result["item"] == "":
        result["item"] = None

    return result
