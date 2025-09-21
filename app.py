from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta
from models import Todo, Class, init_db
from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
import json
from werkzeug.utils import secure_filename
import calendar as cal

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # create folder if it doesn't exist

# ---------------------- APP SETUP ----------------------
app = Flask(__name__)
app.secret_key = "xinyee0766"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')
SUBSCRIPTIONS = []  # kept for backward compatibility

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
init_db()

# Ensure subscriptions table exists
with get_db_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE,
            p256dh TEXT,
            auth TEXT
        )
    """)
    conn.commit()

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------------------- CLASS ROUTES ----------------------
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
        if class_obj:
            conn.execute("DELETE FROM classes WHERE id=?", (class_id,))
            conn.commit()
            flash("Class deleted successfully!", "success")
    return redirect(url_for('index'))

@app.route('/timetable')
def timetable():
    conn = get_db_connection()
    classes = conn.execute("SELECT * FROM classes").fetchall()
    conn.close()

    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("20:00", "%H:%M")
    time_slots = []
    while start <= end:
        time_slots.append(start.strftime("%H:%M"))
        start += timedelta(hours=1)

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

    return render_template('timetable.html', time_slots=time_slots, class_map=class_map)

# ---------------------- TODO ROUTES ----------------------
@app.route("/todos")
def todos():
    search_query = request.args.get("q", "").strip()
    if search_query:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM todos WHERE task LIKE ? ORDER BY due_date",
                (f"%{search_query}%",)
            ).fetchall()
            todos_filtered = [Todo(**dict(r)) for r in rows]
        return render_template("todos.html", todos=todos_filtered, search_query=search_query)
    else:
        all_todos = Todo.all()
        return render_template("todos.html", todos=all_todos)


@app.route("/todos/add", methods=["GET", "POST"])
def add_todo():
    if request.method == "POST":
        task = request.form["task"].strip()
        due_date = request.form["due_date"]
        due_time = request.form.get("due_time")

        todo = Todo(task=task, due_date=due_date, due_time=due_time)
        try:
            todo.save()
        except ValueError as e:
            flash(str(e), "error")
            return render_template("add_todo.html")

        flash("Task added successfully!", "success")
        return redirect(url_for("todos"))
    return render_template("add_todo.html")


@app.route("/todos/edit/<int:todo_id>", methods=["GET", "POST"])
def edit_todo(todo_id):
    todo = Todo.get_by_id(todo_id)
    if not todo:
        flash("Task not found.", "error")
        return redirect(url_for("todos"))

    if request.method == "POST":
        task = request.form["task"].strip()
        due_date = request.form["due_date"]
        due_time = request.form.get("due_time")
        is_done = int("is_done" in request.form)

        todo.task = task
        todo.due_date = due_date
        todo.due_time = due_time
        todo.is_done = is_done

        try:
            todo.save()
        except ValueError as e:
            flash(str(e), "error")
            return render_template("edit_todo.html", todo=todo)

        flash("Task updated successfully!", "success")
        return redirect(url_for("todos"))

    return render_template("edit_todo.html", todo=todo)


# ✅ NEW ROUTE ADDED
@app.route("/todos/delete/<int:todo_id>", methods=["POST"])
def delete_todo(todo_id):
    todo = Todo.get_by_id(todo_id)
    if not todo:
        flash("Task not found.", "error")
        return redirect(url_for("todos"))

    todo.delete()
    flash("Task deleted successfully!", "success")
    return redirect(url_for("todos"))

# ---------------------- NOTIFICATION CHECK ----------------------
@app.route("/todos/check")
def check_due_tasks():
    all_todos = Todo.all()
    now = datetime.now()
    tasks = []

    for t in all_todos:
        if not t.due_date:
            continue
        due_date = datetime.strptime(str(t.due_date), "%Y-%m-%d").date()
        due_time = datetime.strptime(t.due_time, "%H:%M").time() if t.due_time else None

        if due_date == now.date():
            if not due_time or now < datetime.combine(due_date, due_time):
                tasks.append(f"{t.task} (due today)")

        if due_time:
            due_dt = datetime.combine(due_date, due_time)
            if abs((now - due_dt).total_seconds()) < 120:
                tasks.append(f"{t.task} (due now)")
            if abs((now - (due_dt + timedelta(minutes=10))).total_seconds()) < 120:
                tasks.append(f"{t.task} (overdue 10 min)")

    return jsonify({"tasks": tasks})

# ---------------------- PUSH NOTIFICATIONS ----------------------
@app.route("/subscribe", methods=["POST"])
def subscribe():
    subscription_info = request.get_json()
    if subscription_info not in SUBSCRIPTIONS:
        SUBSCRIPTIONS.append(subscription_info)

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO subscriptions (endpoint, p256dh, auth)
            VALUES (?, ?, ?)
        """, (
            subscription_info["endpoint"],
            subscription_info["keys"]["p256dh"],
            subscription_info["keys"]["auth"]
        ))
        conn.commit()

    return jsonify({"success": True})

def send_push_notification(subscription, title, body):
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:xinyee0766@gmail.com"}
        )
        print("Push sent successfully!")
    except WebPushException as ex:
        print("Push failed:", ex)

@app.route("/test_push")
def test_push():
    with get_db_connection() as conn:
        subs = conn.execute("SELECT * FROM subscriptions").fetchall()
    if not subs:
        return "No subscriptions yet!"
    for sub in subs:
        subscription_dict = {
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}
        }
        send_push_notification(subscription_dict, "Test Push", "This is a test notification")
    return "Push sent!"

@app.context_processor
def inject_vapid_key():
    return dict(VAPID_PUBLIC_KEY=VAPID_PUBLIC_KEY)

# ---------------------- BACKGROUND SCHEDULER ----------------------
def check_and_notify():
    now = datetime.now()
    all_todos = Todo.all()
    tasks = []

    for t in all_todos:
        if not t.due_date:
            continue
        due_date = datetime.strptime(str(t.due_date), "%Y-%m-%d").date()
        due_time = datetime.strptime(t.due_time, "%H:%M").time() if t.due_time else None

        if due_time:
            due_dt = datetime.combine(due_date, due_time)
            diff = (now - due_dt).total_seconds()

            if 0 <= diff < 120:   # due now
                tasks.append(f"{t.task} (due now)")
            elif 600 <= diff < 720:  # 10 min overdue
                tasks.append(f"{t.task} (overdue 10 min)")

    if tasks:
        with get_db_connection() as conn:
            subs = conn.execute("SELECT * FROM subscriptions").fetchall()
        for task in tasks:
            for sub in subs:
                subscription_dict = {
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}
                }
                send_push_notification(subscription_dict, "Task Reminder", task)

scheduler = BackgroundScheduler(daemon=True)
if not scheduler.get_jobs():
    scheduler.add_job(check_and_notify, trigger="interval", minutes=1)
scheduler.start()

@app.route("/dashboard/upload", methods=["POST"])
def upload_files():
    # Get all files from the request
    files = request.files.getlist("files[]")
    saved_files = []

    for f in files:
        if f.filename == "":
            continue
        filename = secure_filename(f.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(save_path)
        saved_files.append(filename)

    return jsonify({"uploaded": saved_files})

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/calendar')
def calendar_view():
    # Get current year and month from query parameters or use current date
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    # Calculate previous and next month
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
        
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    # Create calendar matrix
    cal_obj = cal.Calendar(firstweekday=6)  # Sunday as first day (6=Sunday)
    month_days = cal_obj.monthdayscalendar(year, month)
    
    # Convert to our format
    weeks = []
    today = datetime.now().date()
    
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:  # Day from previous/next month
                week_data.append({
                    'day': '',
                    'current_month': False,
                    'is_today': False,
                    'events': []  # Empty events for non-current month days
                })
            else:
                day_date = datetime(year, month, day).date()
                week_data.append({
                    'day': day,
                    'current_month': True,
                    'is_today': (day_date == today),
                    'events': get_events_for_date(day_date)  # Get real events from database
                })
        weeks.append(week_data)
    
    return render_template('calendar.html',
                         calendar=weeks,
                         month_name=datetime(year, month, 1).strftime('%B'),
                         year=year,
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month)

def get_events_for_date(date):
    """Get tasks/events for a specific date from the database"""
    date_str = date.strftime("%Y-%m-%d")
    
    with get_db_connection() as conn:
        # Get todos for this date
        rows = conn.execute(
            "SELECT * FROM todos WHERE due_date = ? ORDER BY due_time",
            (date_str,)
        ).fetchall()
        
        events = []
        for row in rows:
            todo = Todo(**dict(row))
            events.append({
                'id': todo.id,
                'title': todo.task,
                'time': todo.due_time if todo.due_time else 'All Day',
                'color': '#ff8c66' if not todo.is_done else '#888888'  # Orange for pending, gray for completed
            })
        
        return events
    
@app.route('/todo_details/<int:todo_id>')
def todo_details(todo_id):
    todo = Todo.get_by_id(todo_id)
    if not todo:
        flash("Task not found", "error")
        return redirect(url_for('calendar_view'))
    
    return render_template('todo_details.html', todo=todo)
    
# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
