# Approach (200 words)

I built Listy as a Flask + vanilla-JS web app so voice capture could run
entirely in the browser via the Web Speech API — free, instant, and needing
no API key or paid service. Rather than reaching for a heavy NLP library, I
wrote a small regex/keyword intent parser (`nlp_engine.py`) that maps varied
phrasing ("Add milk", "I need apples", "I want to buy bananas") to a single
add/remove/search intent, extracts quantities from both digits and spoken
number words, and detects price ceilings and brand names for search
queries. Multilingual support is keyword-based across four languages,
switching the recognizer's listening language and matching trigger phrases
per language — a lightweight but honest interpretation given the free-tier
constraint.

Items are auto-categorized via a keyword map, and a SQLite-backed history
table powers "you usually buy" suggestions alongside a calendar-based
seasonal table and a static substitutes map. A mock product catalog backs
voice search by name/brand/price.

For UI, I designed the list as a torn-paper receipt inside a dark console,
with live transcript feedback, a listening-state animation, empty/error
states, and a typed-command fallback for unsupported browsers — aiming for
something that reads as intentional rather than a generic form.
