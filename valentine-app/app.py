import json
import os
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
WISHLIST_FILE = os.path.join(BASE_DIR, "wishlist.json")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
HALLOWEEN_FILE = os.path.join(BASE_DIR, "halloween-watchlist.json")


def read_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, items):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


# ── Wish List API ──

@app.route("/api/wishlist", methods=["GET"])
def get_wishlist():
    return jsonify(read_json(WISHLIST_FILE))


@app.route("/api/wishlist", methods=["POST"])
def add_wishlist_item():
    item = request.get_json()
    if not item or not item.get("name"):
        return jsonify({"error": "Name is required"}), 400
    items = read_json(WISHLIST_FILE)
    items.insert(0, item)
    write_json(WISHLIST_FILE, items)
    return jsonify(item), 201


@app.route("/api/wishlist/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(item_id):
    items = read_json(WISHLIST_FILE)
    items = [i for i in items if i.get("id") != item_id]
    write_json(WISHLIST_FILE, items)
    return jsonify({"ok": True})


# ── Watchlist API ──

@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    return jsonify(read_json(WATCHLIST_FILE))


@app.route("/api/watchlist", methods=["POST"])
def add_watchlist_item():
    item = request.get_json()
    if not item or not item.get("title"):
        return jsonify({"error": "Title is required"}), 400
    items = read_json(WATCHLIST_FILE)
    items.insert(0, item)
    write_json(WATCHLIST_FILE, items)
    return jsonify(item), 201


@app.route("/api/watchlist/<int:item_id>", methods=["PUT"])
def update_watchlist_item(item_id):
    data = request.get_json()
    items = read_json(WATCHLIST_FILE)
    for i in items:
        if i.get("id") == item_id:
            i.update(data)
            break
    write_json(WATCHLIST_FILE, items)
    return jsonify({"ok": True})


@app.route("/api/watchlist/<int:item_id>", methods=["DELETE"])
def delete_watchlist_item(item_id):
    items = read_json(WATCHLIST_FILE)
    items = [i for i in items if i.get("id") != item_id]
    write_json(WATCHLIST_FILE, items)
    return jsonify({"ok": True})


# ── Halloween Watchlist API ──

@app.route("/api/halloween-watchlist", methods=["GET"])
def get_halloween():
    return jsonify(read_json(HALLOWEEN_FILE))


@app.route("/api/halloween-watchlist", methods=["POST"])
def add_halloween_item():
    item = request.get_json()
    if not item or not item.get("title"):
        return jsonify({"error": "Title is required"}), 400
    items = read_json(HALLOWEEN_FILE)
    items.insert(0, item)
    write_json(HALLOWEEN_FILE, items)
    return jsonify(item), 201


@app.route("/api/halloween-watchlist/<int:item_id>", methods=["PUT"])
def update_halloween_item(item_id):
    data = request.get_json()
    items = read_json(HALLOWEEN_FILE)
    for i in items:
        if i.get("id") == item_id:
            i.update(data)
            break
    write_json(HALLOWEEN_FILE, items)
    return jsonify({"ok": True})


@app.route("/api/halloween-watchlist/<int:item_id>", methods=["DELETE"])
def delete_halloween_item(item_id):
    items = read_json(HALLOWEEN_FILE)
    items = [i for i in items if i.get("id") != item_id]
    write_json(HALLOWEEN_FILE, items)
    return jsonify({"ok": True})


@app.route("/static/photos/<path:filename>")
def photos(filename):
    return send_from_directory("static/photos", filename)


@app.route("/static/music/<path:filename>")
def music(filename):
    return send_from_directory("static/music", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
