import sqlite3
import sys


def init_db(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'medium'
        )"""
    )
    # Add priority column to existing databases
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()


VALID_PRIORITIES = ("high", "medium", "low")


def add_task(conn):
    desc = input("Enter task description: ").strip()
    if not desc:
        print("Task description cannot be empty.")
        return
    priority = input("Priority (high/medium/low) [medium]: ").strip().lower() or "medium"
    if priority not in VALID_PRIORITIES:
        print("Invalid priority. Using 'medium'.")
        priority = "medium"
    conn.execute("INSERT INTO tasks (description, priority) VALUES (?, ?)", (desc, priority))
    conn.commit()
    print(f'Added: "{desc}" [{priority}]')


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def view_tasks(conn):
    rows = conn.execute(
        "SELECT id, description, completed, priority FROM tasks ORDER BY id"
    ).fetchall()
    if not rows:
        print("No tasks found.")
        return
    rows.sort(key=lambda r: PRIORITY_ORDER.get(r[3], 1))
    print(f"\n{'ID':<5} {'Priority':<10} {'Status':<12} {'Description'}")
    print("-" * 55)
    for task_id, desc, completed, priority in rows:
        status = "[done]" if completed else "[pending]"
        print(f"{task_id:<5} {priority:<10} {status:<12} {desc}")
    print()


def complete_task(conn):
    view_tasks(conn)
    try:
        task_id = int(input("Enter task ID to mark complete: "))
    except ValueError:
        print("Invalid ID.")
        return
    cursor = conn.execute(
        "UPDATE tasks SET completed = 1 WHERE id = ? AND completed = 0", (task_id,)
    )
    conn.commit()
    if cursor.rowcount:
        print(f"Task {task_id} marked as complete.")
    else:
        print("Task not found or already completed.")


def edit_task(conn):
    view_tasks(conn)
    try:
        task_id = int(input("Enter task ID to edit: "))
    except ValueError:
        print("Invalid ID.")
        return
    row = conn.execute(
        "SELECT description, priority FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        print("Task not found.")
        return
    old_desc, old_priority = row
    new_desc = input(f"New description [{old_desc}]: ").strip() or old_desc
    new_priority = input(f"New priority (high/medium/low) [{old_priority}]: ").strip().lower() or old_priority
    if new_priority not in VALID_PRIORITIES:
        print(f"Invalid priority. Keeping '{old_priority}'.")
        new_priority = old_priority
    conn.execute(
        "UPDATE tasks SET description = ?, priority = ? WHERE id = ?",
        (new_desc, new_priority, task_id),
    )
    conn.commit()
    print(f"Task {task_id} updated.")


def delete_task(conn):
    view_tasks(conn)
    try:
        task_id = int(input("Enter task ID to delete: "))
    except ValueError:
        print("Invalid ID.")
        return
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    if cursor.rowcount:
        print(f"Task {task_id} deleted.")
    else:
        print("Task not found.")


def main():
    conn = sqlite3.connect("tasks.db")
    init_db(conn)

    menu = """
===== To-Do List =====
1. Add task
2. View tasks
3. Mark task complete
4. Edit task
5. Delete task
6. Exit
======================"""

    actions = {
        "1": add_task,
        "2": view_tasks,
        "3": complete_task,
        "4": edit_task,
        "5": delete_task,
    }

    try:
        while True:
            print(menu)
            choice = input("Choose an option: ").strip()
            if choice == "6":
                print("Goodbye!")
                break
            action = actions.get(choice)
            if action:
                action(conn)
            else:
                print("Invalid option. Try again.")
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
