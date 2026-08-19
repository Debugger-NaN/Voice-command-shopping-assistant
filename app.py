"""
app.py
Voice Command Shopping Assistant -- Flask backend.

Endpoints
---------
GET    /                       -> serves the single-page UI
GET    /api/list               -> current shopping list
POST   /api/command             -> {text, lang} parse + execute a voice command
PATCH  /api/item/<id>           -> update quantity of an item
DELETE /api/item/<id>           -> remove an item
GET    /api/suggestions         -> frequent / seasonal / substitute suggestions
GET    /api/search?q=&max_price=&brand=  -> voice-activated product search

Storage: SQLite (file-based, zero setup, fine for an assessment/demo).
"""

import os
import sqlite3
from datetime import datetime

from flask import Flask, g, jsonify, render_template, request

import catalog
from nlp_engine import parse_command

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shopping.db")

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit TEXT,
            added_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS history (
            name TEXT PRIMARY KEY,
            times_added INTEGER NOT NULL DEFAULT 0,
            last_added TEXT
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def item_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "added_at": row["added_at"],
    }


# ---------------------------------------------------------------------------
# Routes -- pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes -- API
# ---------------------------------------------------------------------------
@app.get("/api/list")
def get_list():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY category, added_at").fetchall()
    return jsonify([item_to_dict(r) for r in rows])


@app.post("/api/command")
def handle_command():
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "")
    intent = parse_command(text)
    db = get_db()

    if intent["action"] == "add" and intent["item"]:
        name = intent["item"].lower().strip()
        category = catalog.categorize(name)
        now = datetime.utcnow().isoformat()

        existing = db.execute(
            "SELECT * FROM items WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            new_qty = existing["quantity"] + intent["quantity"]
            db.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_qty, existing["id"]))
        else:
            db.execute(
                "INSERT INTO items (name, category, quantity, unit, added_at) VALUES (?,?,?,?,?)",
                (name, category, intent["quantity"], intent["unit"], now),
            )
        db.execute(
            """INSERT INTO history (name, times_added, last_added) VALUES (?, 1, ?)
               ON CONFLICT(name) DO UPDATE SET
                 times_added = times_added + 1,
                 last_added = excluded.last_added""",
            (name, now),
        )
        db.commit()
        substitutes = catalog.get_substitutes(name)
        message = f"Added {intent['quantity']} {intent['unit'] or ''} {name}".strip()
        response = {
            "action": "add",
            "item": name,
            "category": category,
            "quantity": intent["quantity"],
            "message": message,
            "substitutes": substitutes,
        }

    elif intent["action"] == "remove" and intent["item"]:
        name = intent["item"].lower().strip()
        row = db.execute("SELECT * FROM items WHERE name = ?", (name,)).fetchone()
        if row:
            db.execute("DELETE FROM items WHERE id = ?", (row["id"],))
            db.commit()
            response = {"action": "remove", "item": name, "message": f"Removed {name}"}
        else:
            response = {
                "action": "remove",
                "item": name,
                "message": f"{name} wasn't on your list",
                "not_found": True,
            }

    elif intent["action"] == "search" and intent["item"]:
        results = catalog.search_products(
            intent["item"], max_price=intent["max_price"], brand=intent["brand"]
        )
        response = {
            "action": "search",
            "item": intent["item"],
            "max_price": intent["max_price"],
            "brand": intent["brand"],
            "results": results,
            "message": f"Found {len(results)} result(s) for {intent['item']}",
        }

    else:
        response = {
            "action": "unknown",
            "message": "Sorry, I didn't catch an item to add, remove, or search for. "
                       "Try: \"Add two bottles of water\" or \"Remove milk\".",
        }

    response["list"] = [item_to_dict(r) for r in
                         db.execute("SELECT * FROM items ORDER BY category, added_at").fetchall()]
    return jsonify(response)


@app.patch("/api/item/<int:item_id>")
def update_item(item_id):
    payload = request.get_json(force=True, silent=True) or {}
    quantity = payload.get("quantity")
    db = get_db()
    if quantity is None or quantity < 1:
        return jsonify({"error": "quantity must be >= 1"}), 400
    db.execute("UPDATE items SET quantity = ? WHERE id = ?", (quantity, item_id))
    db.commit()
    return jsonify({"ok": True})


@app.delete("/api/item/<int:item_id>")
def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    return jsonify({"ok": True})


@app.get("/api/suggestions")
def suggestions():
    db = get_db()
    frequent_rows = db.execute(
        "SELECT name, times_added FROM history ORDER BY times_added DESC LIMIT 5"
    ).fetchall()
    current_names = {
        r["name"] for r in db.execute("SELECT name FROM items").fetchall()
    }
    frequent = [
        {"name": r["name"], "times_added": r["times_added"]}
        for r in frequent_rows
        if r["name"] not in current_names
    ]
    seasonal = [s for s in catalog.seasonal_suggestions() if s not in current_names]

    return jsonify({
        "frequent": frequent,
        "seasonal": seasonal,
    })


@app.get("/api/search")
def search():
    q = request.args.get("q", "")
    max_price = request.args.get("max_price", type=float)
    brand = request.args.get("brand")
    results = catalog.search_products(q, max_price=max_price, brand=brand)
    return jsonify(results)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # Also initialize when imported by a WSGI server (e.g. gunicorn on Render)
    init_db()
