import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()
c.execute("SELECT DISTINCT day FROM classes")
days = c.fetchall()
for day in days:
    print(day[0])
conn.close()
