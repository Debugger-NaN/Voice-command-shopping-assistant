# 🛒 Listy — Voice Command Shopping Assistant

A voice-first shopping list manager. Speak naturally — "Add milk," "I need
apples," "Find toothpaste under $5" — and Listy parses the intent,
manages your list, and surfaces smart suggestions, entirely through a
browser-based voice interface.

Built for a technical assessment with an 8-hour scope, using a Python
(Flask) backend and vanilla JavaScript frontend, with zero paid APIs.

---

## 🔗 Live demo & repo

| | |
|---|---|
| **Live app** | `https://voice-command-shopping-assistant-avta.onrender.com/` |
| **Repository** | `https://github.com/Debugger-NaN/Voice-command-shopping-assistant` |

---

## 📸 What it looks like

The interface is split into two panels:
- **Left — the voice console**: a mic button, live transcript of what was
  heard, a language selector, and a text-input fallback.
- **Right — the list**: rendered as a torn-paper "receipt," with items
  grouped by category and "you might need" / "in season" suggestion chips
  at the bottom.

---

## ✅ Feature checklist (mapped to the assignment brief)

### 1. Voice Input
- [x] **Voice command recognition** — via the browser's native Web Speech API.
- [x] **Flexible phrasing (NLP)** — a custom parser understands "Add milk",
  "I need apples", "I want to buy bananas" as the same intent.
- [x] **Multilingual support** — recognizer language switch (English,
  Spanish, Hindi, French) with trigger-phrase keyword sets per language.

### 2. Smart Suggestions
- [x] **Product recommendations** — "You usually buy" chips, generated from
  a persisted add-history table (most-frequently-added items not currently
  on your list).
- [x] **Seasonal recommendations** — a calendar-based table suggests
  in-season produce for the current month.
- [x] **Substitutes** — adding an item like milk surfaces alternatives
  (almond milk, soy milk, oat milk) inline in the response.

### 3. Shopping List Management
- [x] **Add / remove / modify items** by voice or typed text.
- [x] **Auto-categorization** — items are sorted into Dairy, Produce,
  Bakery, Meat & Seafood, Snacks, Beverages, Pantry, Household, Other.
- [x] **Quantity management** — parses both digit and spoken-word
  quantities ("2 bottles of water" and "two bottles of water" both work),
  plus units (bottles, kg, dozen, packs, etc.).

### 4. Voice-Activated Search
- [x] **Item search** by name, e.g. "Find me organic apples."
- [x] **Price range filtering** — "Find toothpaste under $5" filters a
  mock product catalog by price ceiling.
- [x] **Brand filtering** — recognizes known brand names in the query.

### 11. UI/UX
- [x] **Minimalist interface** with a clear, single-purpose layout.
- [x] **Visual feedback** — live transcript, listening-state animation,
  inline confirmation messages, animated "printing" of new list items.
- [x] **Mobile-friendly** — responsive down to a single column; the voice
  flow works the same on mobile Chrome.

### 12. Hosting
- [x] Deployable as-is to any Python-friendly free host (Render, Railway,
  Fly.io, PythonAnywhere) — see [Deployment](#-deployment) below.

---

## 🧱 Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3 + Flask | Lightweight, minimal boilerplate, easy to deploy anywhere. |
| Voice capture | Browser Web Speech API | Free, built into Chrome/Edge, no API key, runs client-side. |
| NLP / intent parsing | Custom regex + keyword engine (`nlp_engine.py`) | Transparent, instant, zero external dependency or cold-start latency. |
| Storage | SQLite | Zero-config, file-based, perfect for a single-user demo/assessment. |
| Frontend | Vanilla HTML/CSS/JS | No build step, no framework overhead, fast to load. |
| Fonts | Fraunces, IBM Plex Mono, Inter | Display serif + "receipt printer" mono + clean UI sans. |

No paid AI/ML services are used anywhere in the stack.

---

## 🗂️ Project structure

```
voice-shopping-assistant/
├── app.py                 # Flask routes: list, command, suggestions, search
├── nlp_engine.py           # Regex/keyword intent parser (the "NLP" layer)
├── catalog.py               # Category map, seasonal table, substitutes, mock products
├── requirements.txt         # Flask + gunicorn (only 2 dependencies)
├── templates/
│   └── index.html          # Single-page UI
├── static/
│   ├── css/style.css        # Design system (see Design section)
│   └── js/app.js            # Speech capture, API calls, DOM rendering
├── README.md
├── WRITEUP.md               # 200-word approach write-up (assignment deliverable)
└── .gitignore
```

---

## 🧠 How the NLP engine works

`nlp_engine.py` turns a raw transcript into a structured intent without any
external NLP library:

```python
parse_command("Add two bottles of water")
# -> {
#      "action": "add",
#      "item": "water",
#      "quantity": 2,
#      "unit": "bottles",
#      "max_price": None,
#      "brand": None,
#      "raw": "Add two bottles of water"
#    }
```

**Pipeline:**
1. **Price extraction** — regex matches "under $X" / "less than $X" and
   strips it from the text before further parsing.
2. **Brand detection** — checks the transcript against a known-brands list.
3. **Intent detection** — matches the longest trigger phrase from
   multilingual keyword lists (`ADD_TRIGGERS`, `REMOVE_TRIGGERS`,
   `SEARCH_TRIGGERS`) so "I want to buy" correctly wins over the shorter
   "I want".
4. **Quantity + unit extraction** — a regex pulls a leading number (digit
   or spoken word — "two" is normalized to `2`) and an optional unit
   (bottles, kg, dozen, packs, etc.) from the remaining text.
5. **Fallback** — if no trigger phrase is found, the whole utterance is
   treated as an implicit "add" (so just saying "milk" works).

This keeps the whole NLP layer inspectable in one file — extending it to a
new phrase or language is just adding a string to a list.

---

## 🔌 API reference

All endpoints return JSON.

### `GET /api/list`
Returns the current shopping list.
```json
[
  {"id": 1, "name": "milk", "category": "Dairy", "quantity": 1, "unit": null, "added_at": "2026-08-20T10:00:00"}
]
```

### `POST /api/command`
Parses and executes a voice/text command.
**Request:**
```json
{ "text": "Add two bottles of water" }
```
**Response:**
```json
{
  "action": "add",
  "item": "water",
  "category": "Beverages",
  "quantity": 2,
  "message": "Added 2 bottles water",
  "substitutes": [],
  "list": [ /* full updated list */ ]
}
```
For a `search` action, the response includes a `results` array of matched
products (name, brand, size, price) instead of updating the list.

### `PATCH /api/item/<id>`
Updates an item's quantity.
```json
{ "quantity": 3 }
```

### `DELETE /api/item/<id>`
Removes an item from the list.

### `GET /api/suggestions`
Returns "you usually buy" and "in season" suggestion chips.
```json
{
  "frequent": [{"name": "bread", "times_added": 4}],
  "seasonal": ["grapes", "corn", "tomatoes"]
}
```

### `GET /api/search?q=&max_price=&brand=`
Direct product search (used internally by voice search, also usable
standalone).

---

## 💻 Running locally

```bash
git clone <your-repo-url>
cd voice-shopping-assistant

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in **Chrome or Edge** (the Web Speech API
isn't supported in Firefox or Safari). Click the mic, allow microphone
access, and speak — or use the text box at the bottom of the console panel.

> **Note on microphone access:** the Web Speech API only works on secure
> origins. `localhost` is treated as secure automatically, but accessing
> the app via a raw IP address (e.g. `192.168.x.x:5000`) will be blocked by
> the browser with a `not-allowed` error. Use `localhost` for local testing,
> or deploy to get a real `https://` URL.

---

## 🚀 Deployment

The app is a standard Flask app with no platform-specific code, so it
deploys to any Python host. **Render** (free tier) is the simplest option
and gives you a real HTTPS URL, which is required for the mic to work in
production.

1. Push this repo to GitHub (public, `main` branch).
2. On [render.com](https://render.com) → **New** → **Web Service** → connect
   the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Instance type: **Free**
6. Deploy — Render provisions an `https://your-app.onrender.com` URL
   automatically.

Alternative free hosts that work the same way: Railway, Fly.io,
PythonAnywhere.

> Free-tier note: Render's free instances sleep after ~15 minutes of
> inactivity, so the first request after idling can take 30–60 seconds to
> wake up. This is expected behavior, not a bug.

---

## 🎨 Design

The shopping list is rendered as a torn-paper receipt (perforated top and
bottom edges, done with a CSS zigzag gradient) inside a dark evergreen
console. New items animate in as if being "printed" onto the receipt.

**Palette:** deep evergreen `#0F1D17` (console) · warm paper `#FBF7EE`
(receipt) · mint `#7FBF9E` (primary accent) · gold `#D8A93B`
(suggestions/seasonal).

**Type:** Fraunces (display serif, headings) · IBM Plex Mono (the receipt
itself, echoing a real receipt printer) · Inter (UI chrome/labels).

---

## ⚠️ Known limitations & honest tradeoffs

These are deliberate scope decisions given the free-tier / 8-hour
constraint, documented here rather than hidden:

- **Multilingual support is keyword-based, not translation-based.** The
  recognizer switches listening language and trigger phrases are matched
  in four languages, but item names themselves aren't translated to a
  canonical form. A production version would insert a translation API
  step between speech-to-text and intent parsing.
- **Product catalog is mocked**, not a real inventory/pricing API — swap
  `catalog.py`'s `PRODUCT_CATALOG` for a real product API call in
  production.
- **Single shared list, no accounts/auth** — fine for a demo, would need
  a user model for multi-user use.
- **Web Speech API browser support** — works in Chrome/Edge; Firefox and
  Safari fall back to the text input.

## 🔮 What I'd add with more time

- A speech-to-text fallback (e.g. a free-tier Whisper endpoint) for
  browsers without Web Speech API support.
- A real translation layer for genuinely multilingual item names.
- User accounts and persisted per-user lists.
- A real product/pricing API instead of the mock catalog.
- `pytest` unit tests around `nlp_engine.parse_command` for the full set
  of example phrasings.

---

## 🧪 Testing notes

`nlp_engine.parse_command` and the `/api/command` endpoint were manually
verified against every example phrase in the assignment brief: "Add milk",
"I need apples", "I want to buy bananas", "Remove milk from my list",
"Add 2 bottles of water" / "two bottles of water", and "Find toothpaste
under $5" — all resolve to the correct action, item, quantity, and filters.

---

## 📄 License

Built as a technical assessment submission. Free to reference or adapt.
