import sqlite3
import os
from models import init_db, Class

DB_NAME = os.path.join(os.path.dirname(__file__), "database.db")

def migrate_old_time_column(conn):
    """Check for old 'time' column and migrate data if needed."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(classes)")
    columns = [col[1] for col in c.fetchall()]

    if 'time' in columns:
        print("Old 'time' column detected. Migrating data...")

        # Rename old table
        c.execute("ALTER TABLE classes RENAME TO old_classes")

        # Create new table
        c.execute('''
            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT NOT NULL,
                notes TEXT
            )
        ''')

        # Copy data from old table
        c.execute('''
            INSERT INTO classes (id, name, day, start_time, end_time, location, notes)
            SELECT id, name, day, time, time, location, notes FROM old_classes
        ''')

        # Drop old table
        c.execute("DROP TABLE old_classes")
        print("Table updated successfully!")
    else:
        print("No old 'time' column found. No changes made.")

    conn.commit()

def add_sample_classes():
    if not Class.get_all():
        print("Adding sample classes for testing...")
        sample_classes = [
            Class(name="CSP1123 - Mini IT Project", day="Monday", start_time="09:00", end_time="10:30", location="CQCR3003", notes="Project meeting"),
            Class(name="CSP2101 - Data Structures", day="Tuesday", start_time="11:00", end_time="12:30", location="CQCR2001", notes="Lab session"),
            Class(name="CSP3302 - AI Basics", day="Wednesday", start_time="14:00", end_time="15:30", location="CQCR4002", notes="Lecture"),
        ]
        for c in sample_classes:
            c.save()
        print(f"✅ Added {len(sample_classes)} sample classes.")

def update_db():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    migrate_old_time_column(conn)
    conn.close()
    add_sample_classes()

if __name__ == "__main__":
    update_db()
    print("✅ Database update complete.")