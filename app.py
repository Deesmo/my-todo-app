import os
import sqlite3
from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)

# PostgreSQL support: use DATABASE_URL if set (Render provides this), else SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)
DATABASE = "tasks.db"
VALID_PRIORITIES = ("high", "medium", "low")


def get_db():
    if "db" not in g:
        if USE_POSTGRES:
            import psycopg2
            import psycopg2.extras
            g.db = psycopg2.connect(DATABASE_URL)
            g.db.autocommit = False
        else:
            g.db = sqlite3.connect(DATABASE)
            g.db.row_factory = sqlite3.Row
    return g.db


def _execute(db, sql, params=()):
    """Execute SQL, translating ? placeholders to %s for PostgreSQL."""
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
    cur = db.cursor() if USE_POSTGRES else db
    cur.execute(sql, params)
    return cur


def _fetchall(db, sql, params=()):
    if USE_POSTGRES:
        import psycopg2.extras
        sql = sql.replace("?", "%s")
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return cur.fetchall()
    else:
        return [dict(r) for r in db.execute(sql, params).fetchall()]


def _fetchone(db, sql, params=()):
    if USE_POSTGRES:
        import psycopg2.extras
        sql = sql.replace("?", "%s")
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return cur.fetchone()
    else:
        row = db.execute(sql, params).fetchone()
        return dict(row) if row else None


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    if USE_POSTGRES:
        cur = db.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                description TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT DEFAULT NULL
            )"""
        )
        db.commit()
    else:
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
    db = get_db()
    tasks = _fetchall(db, "SELECT id, description, completed, priority, due_date FROM tasks ORDER BY id")
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
    if USE_POSTGRES:
        cur = db.cursor()
        import psycopg2.extras
        cur2 = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO tasks (description, priority, due_date) VALUES (%s, %s, %s) RETURNING id",
            (description, priority, due_date),
        )
        new_id = cur.fetchone()[0]
        db.commit()
        cur2.execute(
            "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = %s",
            (new_id,),
        )
        task = cur2.fetchone()
    else:
        cursor = db.execute(
            "INSERT INTO tasks (description, priority, due_date) VALUES (?, ?, ?)",
            (description, priority, due_date),
        )
        db.commit()
        task = _fetchone(db, "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
                         (cursor.lastrowid,))
    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def edit_task(task_id):
    data = request.get_json()
    db = get_db()
    row = _fetchone(db, "SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not row:
        return jsonify({"error": "Task not found"}), 404
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Description is required"}), 400
    priority = (data.get("priority") or "medium").lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    due_date = data.get("due_date")
    _execute(db,
        "UPDATE tasks SET description = ?, priority = ?, due_date = ? WHERE id = ?",
        (description, priority, due_date, task_id),
    )
    db.commit()
    task = _fetchone(db,
        "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
        (task_id,),
    )
    return jsonify(task)


@app.route("/api/tasks/<int:task_id>/complete", methods=["PUT"])
def toggle_complete(task_id):
    db = get_db()
    row = _fetchone(db, "SELECT id, completed FROM tasks WHERE id = ?", (task_id,))
    if not row:
        return jsonify({"error": "Task not found"}), 404
    new_status = 0 if row["completed"] else 1
    _execute(db, "UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))
    db.commit()
    task = _fetchone(db,
        "SELECT id, description, completed, priority, due_date FROM tasks WHERE id = ?",
        (task_id,),
    )
    return jsonify(task)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    db = get_db()
    cur = _execute(db, "DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if USE_POSTGRES:
        if cur.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404
    else:
        if not cur.rowcount:
            return jsonify({"error": "Task not found"}), 404
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
