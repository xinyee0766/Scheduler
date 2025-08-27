from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "xinyee0766"
DB_NAME = "database.db"

def get_db_connection():
    """Return a DB connection that returns rows as dict-like objects"""
    conn = sqlite3.connect(DB_NAME, timeout=10)  # wait 10s if DB is locked
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
    """Home page - shows all classes, with optional search"""
    search_query = request.args.get("q", "").strip()

    with get_db_connection() as conn:
        if search_query:
            classes = conn.execute(
                "SELECT * FROM classes WHERE name LIKE ?",
                (f"%{search_query}%",)
            ).fetchall()
        else:
            classes = conn.execute("SELECT * FROM classes").fetchall()

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

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO classes (name, day, start_time, end_time, location, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (name, day, start_time, end_time, location, notes)
            )
            conn.commit()

        flash("Class added successfully!", "success")
        return redirect(url_for("timetable"))

    return render_template("add_class.html")


@app.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    """Edit an existing class with start and end time"""
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()

        if not class_obj:
            flash('Class not found', 'error')
            return redirect(url_for('timetable'))

        if request.method == 'POST':
            name = request.form.get('name')
            day = request.form.get('day')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            location = request.form.get('location')
            notes = request.form.get('notes', '')

            if not all([name, day, start_time, end_time, location]):
                flash('Please fill in all required fields', 'error')
                return render_template('edit_class.html', class_obj=class_obj)

            conn.execute(
                "UPDATE classes SET name=?, day=?, start_time=?, end_time=?, location=?, notes=? WHERE id=?",
                (name, day, start_time, end_time, location, notes, class_id)
            )
            conn.commit()

            flash('Class updated successfully!', 'success')
            return redirect(url_for('timetable'))

    return render_template('edit_class.html', class_obj=class_obj)


@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    """Delete a class"""
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()

        if not class_obj:
            flash('Class not found', 'error')
            return redirect(url_for('timetable'))

        conn.execute("DELETE FROM classes WHERE id=?", (class_id,))
        conn.commit()

    flash('Class deleted successfully!', 'success')
    return redirect(url_for('timetable'))


@app.route('/timetable')
def timetable():
    conn = get_db_connection()
    classes = conn.execute("SELECT * FROM classes").fetchall()
    conn.close()

    time_slots = [f"{hour:02d}:00" for hour in range(8, 21)]

    class_map = {day: {} for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']}
    for c in classes:
        start_hour = int(c['start_time'].split(":")[0])
        end_hour = int(c['end_time'].split(":")[0])
        for hour in range(start_hour, end_hour + 1):
            class_map[c['day']][f"{hour:02d}:00"] = c

    return render_template('timetable.html', time_slots=time_slots, class_map=class_map)



if __name__ == "__main__":
    app.run(debug=True)
