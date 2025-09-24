import sqlite3
import os

# Use the same database as your Flask app
DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Create the journal table if it doesn't exist
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

print("✅ Journal table created successfully in classes.db!")
