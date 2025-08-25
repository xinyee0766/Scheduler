from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    conn.close()
    return render_template("index.html", classes=classes)

@app.route("/add_class", methods=["POST"])
def add_class():
    name = request.form["name"]
    day = request.form["day"]
    time = request.form["time"]
    location = request.form["location"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO classes (name, day, time, location) VALUES (?, ?, ?, ?)",
              (name, day, time, location))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/delete_class/<int:id>")
def delete_class(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM classes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
