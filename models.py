import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')

def get_db_connection():
    """Return a DB connection with row access by column name."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with classes table if it doesn't exist."""
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

class Class:
    """Class representing a scheduled class"""
    
    def __init__(self, id=None, name="", day="", start_time="", end_time="", location="", notes=""):
        self.id = id
        self.name = name
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.notes = notes

    def save(self):
        """Insert or update the class in the database."""
        conn = get_db_connection()
        c = conn.cursor()
        if self.id:
            c.execute('''
                UPDATE classes
                SET name=?, day=?, start_time=?, end_time=?, location=?, notes=?
                WHERE id=?
            ''', (self.name, self.day, self.start_time, self.end_time, self.location, self.notes, self.id))
        else:
            c.execute('''
                INSERT INTO classes (name, day, start_time, end_time, location, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.name, self.day, self.start_time, self.end_time, self.location, self.notes))
            self.id = c.lastrowid
        conn.commit()
        conn.close()
        return True

    def delete(self):
        """Delete the class from the database."""
        if not self.id:
            return False
        conn = get_db_connection()
        conn.execute("DELETE FROM classes WHERE id=?", (self.id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_all():
        """Return all classes ordered by day and start time."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM classes ORDER BY day, start_time')
        classes = [Class(
            id=row['id'],
            name=row['name'],
            day=row['day'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            location=row['location'],
            notes=row['notes']
        ) for row in c.fetchall()]
        conn.close()
        return classes

    @staticmethod
    def get_by_id(class_id):
        """Return a single class by ID."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        conn.close()
        if row:
            return Class(
                id=row['id'],
                name=row['name'],
                day=row['day'],
                start_time=row['start_time'],
                end_time=row['end_time'],
                location=row['location'],
                notes=row['notes']
            )
        return None

    @staticmethod
    def search(query):
        """Search classes by name."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM classes WHERE name LIKE ? ORDER BY day, start_time',
                  ('%' + query + '%',))
        classes = [Class(
            id=row['id'],
            name=row['name'],
            day=row['day'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            location=row['location'],
            notes=row['notes']
        ) for row in c.fetchall()]
        conn.close()
        return classes
