# Listy — Voice Command Shopping Assistant

A voice-first shopping list manager: speak naturally, and it adds, removes,
searches, and suggests items for you. Built as a Python web app (Flask +
vanilla JS) per the assignment's technical scope and an 8-hour time budget.

## Live demo / repo
- App URL: _add your deployed URL here after hosting (see **Deploying** below)_
- Repo: _add your GitHub URL here_

## Features implemented

| Area | What's implemented |
|---|---|
| Voice input | Browser-native Web Speech API captures speech; flexible phrasing handled by a regex/keyword NLP layer (`nlp_engine.py`) — "Add milk", "I need apples", "I want to buy bananas" all resolve to the same intent. |
| Multilingual | Language selector (English, Spanish, Hindi, French) switches the recognizer's language; trigger-phrase keyword sets exist for all four so the same intents are recognized across languages. |
| Smart suggestions | "You usually buy" (based on stored add-history), "In season" (calendar-based seasonal table), and per-item substitute suggestions (e.g. adding milk surfaces almond/soy/oat milk). |
| List management | Add / remove / update quantity, all voice- or text-driven; items are auto-categorized (Dairy, Produce, Bakery, etc.) via a keyword map. |
| Quantity parsing | Handles both digits and spoken number words: "2 bottles of water" and "two bottles of water" both parse to `quantity=2, unit=bottles`. |
| Voice-activated search | "Find toothpaste under $5" / "Find me organic apples" queries a mock product catalog by name, brand, and price ceiling, shown in a results modal. |
| UI/UX | Minimalist two-pane layout: voice console + a list rendered as a paper "receipt". Live transcript feedback, listening-state animation, loading/empty states, mobile-responsive down to one column. |
| Error handling | Unrecognized commands get an explicit, helpful message instead of failing silently; mic permission/browser-support errors are surfaced in the UI; a text-input fallback exists for unsupported browsers or noisy environments. |

## Architecture

```
templates/index.html    single-page UI (voice console + receipt list)
static/css/style.css    design system (see "Design" below)
static/js/app.js        Web Speech API capture, fetches, rendering
app.py                  Flask routes (list, command, suggestions, search)
nlp_engine.py           regex/keyword command parser (no external NLP dep)
catalog.py              category map, seasonal table, substitutes, mock products
shopping.db             SQLite, created automatically on first run
```

**Why this stack:** the assignment allows any framework and any free-tier
AI/ML service. Rather than wiring in a paid NLP or speech API, this uses two
things that are free and instant everywhere:
1. The **Web Speech API**, built into Chrome/Edge, for actual speech-to-text
   — zero setup, zero API key, runs entirely client-side.
2. A **hand-written intent parser** for turning that transcript into
   add/remove/search actions. It's transparent, has no cold-start latency,
   and is easy to extend with new phrasings or languages by adding to the
   keyword lists in `nlp_engine.py`.

**Honest limitation:** multilingual support here is *keyword-based*, not a
true translation layer — it recognizes trigger phrases in four languages,
but item names beyond that aren't translated. A production version would
add a translation API (e.g. Google Translate) between the recognizer and
the parser so any language's item names normalize to a canonical list.

## Running locally

```bash
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python3 app.py
```

Open `http://localhost:5000`. Click the mic, allow microphone access, and
speak. (Voice recognition requires Chrome or Edge; other browsers fall back
to the text box at the bottom of the console panel.)

## Deploying (per the "reliable platform" requirement)

The app is a standard Flask app with a `requirements.txt` and no
platform-specific code, so it deploys as-is to any of these free tiers:

**Render (recommended, free tier, ~2 minutes):**
1. Push this repo to GitHub.
2. On [render.com](https://render.com) → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy — Render gives you a public HTTPS URL. Voice input needs HTTPS,
   which Render provides by default.

**Alternative — Railway / PythonAnywhere / Fly.io:** same idea — install
`requirements.txt`, run `gunicorn app:app` (or `python app.py` for a quick
test), and use the platform's free HTTPS URL.

> Note: this repository contains the working code, but does not include a
> live deployment, since that requires an account on the hosting platform.
> Follow the steps above to get a public URL for submission.

## Design

The list is rendered as a torn paper "receipt" (perforated top/bottom
edges) inside a dark evergreen console — items visually "print" onto the
list as you add them. Fraunces (display serif) for headings, IBM Plex Mono
for the receipt itself (a nod to real receipt printers), Inter for UI
chrome. Palette: deep evergreen (`#0F1D17`) console, warm paper
(`#FBF7EE`) receipt, mint (`#7FBF9E`) as the primary accent, gold
(`#D8A93B`) for suggestions/seasonal items.

## Testing notes

`nlp_engine.py` and `app.py` were exercised with the example phrases from
the assignment brief ("Add milk", "I need apples", "I want to buy
bananas", "Remove milk from my list", "Add 2 bottles of water" / "two
bottles of water", "Find toothpaste under $5") — all resolve correctly.
For a production submission, add `pytest` unit tests around
`nlp_engine.parse_command`.

## What I'd add with more time

- Real speech-to-text fallback (e.g. Whisper free tier) for browsers
  without Web Speech API support.
- A translation step for genuinely multilingual item names.
- Persisted user accounts instead of a single shared list.
- A real product/price API instead of the mock catalog.
