import sqlite3
from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)
DATABASE = "tasks.db"
VALID_PRIORITIES = ("high", "medium", "low")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'medium'
        )"""
    )
    try:
        db.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    db.commit()


with app.app_context():
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tasks")
def get_tasks():
    rows = get_db().execute(
        "SELECT id, description, completed, priority, due_date FROM tasks ORDER BY id"
    ).fetchall()
    tasks = [dict(r) for r in rows]
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json()
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Description is required"}), 400
    priority = (data.get("priority") or "medium").lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    due_date = data.get("due_date") or None
    db = get_db()
    cursor = db.execute(
        "INSERT INTO tasks (description, priority, due_date) VALUES (?, ?, ?)",
        (description, priority, due_date),
    )
    db.commit()
    task = db.execute(
        "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify(dict(task)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def edit_task(task_id):
    data = request.get_json()
    db = get_db()
    row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return jsonify({"error": "Task not found"}), 404
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Description is required"}), 400
    priority = (data.get("priority") or "medium").lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    due_date = data.get("due_date")
    db.execute(
        "UPDATE tasks SET description = ?, priority = ?, due_date = ? WHERE id = ?",
        (description, priority, due_date, task_id),
    )
    db.commit()
    task = db.execute(
        "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    return jsonify(dict(task))


@app.route("/api/tasks/<int:task_id>/complete", methods=["PUT"])
def toggle_complete(task_id):
    db = get_db()
    row = db.execute(
        "SELECT id, completed FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Task not found"}), 404
    new_status = 0 if row["completed"] else 1
    db.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))
    db.commit()
    task = db.execute(
        "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    return jsonify(dict(task))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if not cursor.rowcount:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
