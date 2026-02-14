import json
import os
import sqlite3
from flask import Flask, render_template, send_from_directory, request, jsonify, g

app = Flask(__name__)

# Store database in persistent location (configurable via env var)
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "valentine.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS halloween (
        id INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.commit()
    db.close()


init_db()


@app.route("/")
def index():
    return render_template("index.html")


# ── Generic helpers ──

def get_all(table):
    rows = get_db().execute(f"SELECT id, data FROM {table} ORDER BY created_at DESC").fetchall()
    items = []
    for row in rows:
        item = json.loads(row["data"])
        item["id"] = row["id"]
        items.append(item)
    return items


def add_item(table, item):
    data = json.dumps(item, ensure_ascii=False)
    cur = get_db().execute(f"INSERT INTO {table} (data) VALUES (?)", (data,))
    get_db().commit()
    item["id"] = cur.lastrowid
    return item


def update_item(table, item_id, updates):
    row = get_db().execute(f"SELECT data FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if row:
        item = json.loads(row["data"])
        item.update(updates)
        get_db().execute(f"UPDATE {table} SET data = ? WHERE id = ?",
                         (json.dumps(item, ensure_ascii=False), item_id))
        get_db().commit()
    return True


def delete_item(table, item_id):
    get_db().execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    get_db().commit()
    return True


# ── Wish List API ──

@app.route("/api/wishlist", methods=["GET"])
def get_wishlist():
    return jsonify(get_all("wishlist"))


@app.route("/api/wishlist", methods=["POST"])
def add_wishlist_item():
    item = request.get_json()
    if not item or not item.get("name"):
        return jsonify({"error": "Name is required"}), 400
    return jsonify(add_item("wishlist", item)), 201


@app.route("/api/wishlist/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(item_id):
    delete_item("wishlist", item_id)
    return jsonify({"ok": True})


# ── Watchlist API ──

@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    return jsonify(get_all("watchlist"))


@app.route("/api/watchlist", methods=["POST"])
def add_watchlist_item():
    item = request.get_json()
    if not item or not item.get("title"):
        return jsonify({"error": "Title is required"}), 400
    return jsonify(add_item("watchlist", item)), 201


@app.route("/api/watchlist/<int:item_id>", methods=["PUT"])
def update_watchlist_item(item_id):
    data = request.get_json()
    update_item("watchlist", item_id, data)
    return jsonify({"ok": True})


@app.route("/api/watchlist/<int:item_id>", methods=["DELETE"])
def delete_watchlist_item(item_id):
    delete_item("watchlist", item_id)
    return jsonify({"ok": True})


# ── Halloween Watchlist API ──

@app.route("/api/halloween-watchlist", methods=["GET"])
def get_halloween():
    return jsonify(get_all("halloween"))


@app.route("/api/halloween-watchlist", methods=["POST"])
def add_halloween_item():
    item = request.get_json()
    if not item or not item.get("title"):
        return jsonify({"error": "Title is required"}), 400
    return jsonify(add_item("halloween", item)), 201


@app.route("/api/halloween-watchlist/<int:item_id>", methods=["PUT"])
def update_halloween_item(item_id):
    data = request.get_json()
    update_item("halloween", item_id, data)
    return jsonify({"ok": True})


@app.route("/api/halloween-watchlist/<int:item_id>", methods=["DELETE"])
def delete_halloween_item(item_id):
    delete_item("halloween", item_id)
    return jsonify({"ok": True})


@app.route("/static/photos/<path:filename>")
def photos(filename):
    return send_from_directory("static/photos", filename)


@app.route("/static/music/<path:filename>")
def music(filename):
    return send_from_directory("static/music", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
