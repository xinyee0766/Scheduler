from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "xinyee0766"
DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

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

init_db()

@app.route("/", methods=["GET"])
def index():
    search_query = request.args.get("q", "").strip()
    with get_db_connection() as conn:
        if search_query:
            classes = conn.execute(
                "SELECT * FROM classes WHERE name LIKE ? ORDER BY day, start_time",
                (f"%{search_query}%",)
            ).fetchall()
        else:
            classes = conn.execute("SELECT * FROM classes ORDER BY day, start_time").fetchall()
    return render_template("classes.html", classes=classes, search_query=search_query)

@app.route("/add_class", methods=["GET", "POST"])
def add_class():
    if request.method == "POST":
        name = request.form.get("name")
        day = request.form.get("day")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        location = request.form.get("location")
        notes = request.form.get("notes", "")

        if not all([name, day, start_time, end_time, location]):
            flash("Please fill in all required fields", "error")
            return render_template("add_class.html")

        if start_time >= end_time:
            flash("Start time must be earlier than end time", "error")
            return render_template("add_class.html")

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO classes (name, day, start_time, end_time, location, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (name, day, start_time, end_time, location, notes)
            )
            conn.commit()

        flash("Class added successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add_class.html")

@app.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        if not class_obj:
            flash("Class not found", "error")
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form.get("name")
            day = request.form.get("day")
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            location = request.form.get("location")
            notes = request.form.get("notes", "")

            if not all([name, day, start_time, end_time, location]):
                flash("Please fill in all required fields", "error")
                return render_template('edit_class.html', class_obj=class_obj)

            if start_time >= end_time:
                flash("Start time must be earlier than end time", "error")
                return render_template('edit_class.html', class_obj=class_obj)

            conn.execute(
                "UPDATE classes SET name=?, day=?, start_time=?, end_time=?, location=?, notes=? WHERE id=?",
                (name, day, start_time, end_time, location, notes, class_id)
            )
            conn.commit()
            flash("Class updated successfully!", "success")
            return redirect(url_for('index'))

    return render_template('edit_class.html', class_obj=class_obj)

@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        if not class_obj:
            flash("Class not found", "error")
            return redirect(url_for('index'))

        conn.execute("DELETE FROM classes WHERE id=?", (class_id,))
        conn.commit()
    flash("Class deleted successfully!", "success")
    return redirect(url_for('index'))

@app.route('/timetable')
def timetable():
    conn = get_db_connection()
    classes = conn.execute("SELECT * FROM classes").fetchall()
    conn.close()

    # Hourly slots
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("20:00", "%H:%M")
    time_slots = []
    while start <= end:
        time_slots.append(start.strftime("%H:%M"))
        start += timedelta(hours=1)

    # Build class map
    class_map = {day: {slot: [] for slot in time_slots} for day in
                 ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']}

    for c in classes:
        s_time = datetime.strptime(c['start_time'], "%H:%M")
        e_time = datetime.strptime(c['end_time'], "%H:%M")
        for slot in time_slots:
            slot_start = datetime.strptime(slot, "%H:%M")
            slot_end = slot_start + timedelta(hours=1)
            if s_time < slot_end and e_time > slot_start:
                class_map[c['day']][slot].append({
                    'id': c['id'],
                    'name': c['name'],
                    'start_time': c['start_time'],
                    'end_time': c['end_time'],
                    'location': c['location'],
                    'notes': c['notes']
                })

    return render_template('timetable.html',
                           time_slots=time_slots,
                           class_map=class_map)


if __name__ == "__main__":
    app.run(debug=True)
