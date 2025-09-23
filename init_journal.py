import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    mood INTEGER NOT NULL,
    energy INTEGER NOT NULL,
    notes TEXT
)
""")

conn.commit()
conn.close()

print("✅ Journal table created successfully!")
