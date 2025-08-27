import sqlite3

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("PRAGMA table_info(classes)")
columns = [col[1] for col in c.fetchall()]

if 'time' in columns:
    print("Old 'time' column detected. Updating table...")

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

    c.execute('''
        INSERT INTO classes (id, name, day, start_time, end_time, location, notes)
        SELECT id, name, day, time, time, location, notes FROM old_classes
    ''')

    c.execute("DROP TABLE old_classes")

    print("Table updated successfully!")

else:
    print("No old 'time' column found. No changes made.")

conn.commit()
conn.close()
