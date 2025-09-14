import sqlite3
import os
from datetime import date

# Database file path
DB_NAME = os.path.join(os.path.dirname(__file__), "classes.db")

# ---------------------- DB CONNECTION ----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------- INIT DB ----------------------
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT NOT NULL,
                notes TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                due_date TEXT NOT NULL,
                due_time TEXT,
                is_done INTEGER DEFAULT 0
            )
        ''')

# ---------------------- CLASS MODEL ----------------------
class Class:
    def __init__(self, id=None, name="", day="", start_time="", end_time="", location="", notes=""):
        self.id = id
        self.name = name
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.notes = notes

    @staticmethod
    def all():
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM classes ORDER BY day, start_time").fetchall()
            return [Class(**dict(r)) for r in rows]

    @staticmethod
    def get(class_id):
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
            return Class(**dict(row)) if row else None

    def save(self):
        with get_db_connection() as conn:
            if self.id:
                conn.execute('''
                    UPDATE classes
                    SET name=?, day=?, start_time=?, end_time=?, location=?, notes=?
                    WHERE id=?
                ''', (self.name, self.day, self.start_time, self.end_time, self.location, self.notes, self.id))
            else:
                cursor = conn.execute('''
                    INSERT INTO classes (name, day, start_time, end_time, location, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.name, self.day, self.start_time, self.end_time, self.location, self.notes))
                self.id = cursor.lastrowid

    def delete(self):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM classes WHERE id=?", (self.id,))

# ---------------------- TODO MODEL ----------------------
class Todo:
    def __init__(self, id=None, task="", due_date="", due_time=None, is_done=0):
        self.id = id
        self.task = task
        self.due_date = due_date
        self.due_time = due_time
        self.is_done = is_done

    @staticmethod
    def all():
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM todos ORDER BY due_date, due_time").fetchall()
            return [Todo(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(todo_id):
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM todos WHERE id=?", (todo_id,)).fetchone()
            return Todo(**dict(row)) if row else None

    @staticmethod
    def get_due_today():
        today_str = date.today().strftime("%Y-%m-%d")
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM todos WHERE due_date=?", (today_str,)).fetchall()
            return [Todo(**dict(r)) for r in rows]

    def save(self):
        with get_db_connection() as conn:
            if self.id:
                conn.execute('''
                    UPDATE todos SET task=?, due_date=?, due_time=?, is_done=? WHERE id=?
                ''', (self.task, self.due_date, self.due_time, self.is_done, self.id))
            else:
                cursor = conn.execute('''
                    INSERT INTO todos (task, due_date, due_time, is_done)
                    VALUES (?, ?, ?, ?)
                ''', (self.task, self.due_date, self.due_time, self.is_done))
                self.id = cursor.lastrowid

    def delete(self):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM todos WHERE id=?", (self.id,))
