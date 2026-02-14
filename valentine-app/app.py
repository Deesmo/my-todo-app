import json
import os
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

WISHLIST_FILE = os.path.join(os.path.dirname(__file__), "wishlist.json")


def read_wishlist():
    if not os.path.exists(WISHLIST_FILE):
        return []
    with open(WISHLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_wishlist(items):
    with open(WISHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/wishlist", methods=["GET"])
def get_wishlist():
    return jsonify(read_wishlist())


@app.route("/api/wishlist", methods=["POST"])
def add_wishlist_item():
    item = request.get_json()
    if not item or not item.get("name"):
        return jsonify({"error": "Name is required"}), 400
    items = read_wishlist()
    items.insert(0, item)
    write_wishlist(items)
    return jsonify(item), 201


@app.route("/api/wishlist/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(item_id):
    items = read_wishlist()
    items = [i for i in items if i.get("id") != item_id]
    write_wishlist(items)
    return jsonify({"ok": True})


@app.route("/static/photos/<path:filename>")
def photos(filename):
    return send_from_directory("static/photos", filename)


@app.route("/static/music/<path:filename>")
def music(filename):
    return send_from_directory("static/music", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
