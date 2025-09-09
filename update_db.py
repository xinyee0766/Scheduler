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

    c.execute("SELECT id, name, day, time, location, notes FROM old_classes")
    rows = c.fetchall()

    for row in rows:
        id_, name, day, time_value, location, notes = row

        start_time = time_value
        end_time = time_value

        if "-" in time_value:
            parts = time_value.split("-")
            if len(parts) == 2:
                start_time = parts[0].strip()
                end_time = parts[1].strip()

        c.execute('''
            INSERT INTO classes (id, name, day, start_time, end_time, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_, name, day, start_time, end_time, location, notes))

    c.execute("DROP TABLE old_classes")

    print("Table updated successfully! Times were split into start_time and end_time.")

else:
    print("No old 'time' column found. No changes made.")

conn.commit()
conn.close()
