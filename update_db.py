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

        c.execute("ALTER TABLE classes RENAME TO old_classes")

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

        old_rows = c.execute("SELECT id, name, day, time, location, notes FROM old_classes").fetchall()

        for row in old_rows:
            id_, name, day, time_range, location, notes = row
            if "-" in time_range:
                start_time, end_time = [t.strip() for t in time_range.split("-", 1)]
            else:
                start_time = end_time = time_range.strip()
            c.execute('''
                INSERT INTO classes (id, name, day, start_time, end_time, location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_, name, day, start_time, end_time, location, notes))

        c.execute("DROP TABLE old_classes")
        print("✅ Migration completed successfully!")
    else:
        print("ℹ️ No old 'time' column found. No migration needed.")


def update_db():
    """Initialize DB, migrate old data, add sample classes."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    init_db()

    migrate_old_time_column(conn)

    conn.commit()
    conn.close()

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


if __name__ == "__main__":
    update_db()
    print("✅ Database update complete.")
