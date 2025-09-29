from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta, date
from models import Todo, Class, init_db, UploadedFile, Journal
from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
import json
from werkzeug.utils import secure_filename
import calendar as cal
from pyfcm import FCMNotification

from fcm_config import FCM_API_KEY

# ---------------------- FCM SETUP ----------------------
push_service = FCMNotification(FCM_API_KEY)

# ---------------------- IN-MEMORY STORAGE ----------------------
reminders = []
reminder_history = []
notes = []

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------- APP SETUP ----------------------
app = Flask(__name__)
app.secret_key = "xinyee0766"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reminders.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app)


with app.app_context():
    init_db()

DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')
SUBSCRIPTIONS = []

def load_data():
    global reminders, reminder_history, notes
    if os.path.exists('reminders.json'):
        with open('reminders.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            reminders = data.get('reminders', [])
            reminder_history = data.get('history', [])
            notes = data.get('notes', [])

def save_data():
    data = {
        'reminders': reminders,
        'history': reminder_history,
        'notes': notes
    }
    with open('reminders.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load_data()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database models in external init_db (existing) and ensure our tables exist
init_db()

with get_db_connection() as conn:
    # subscriptions table (already in your file) left as-is
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE,
            p256dh TEXT,
            auth TEXT
        )
    """)
    # uploaded_files as before
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            path TEXT
        )
    """)
    # new: reminders table to persist reminders
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            category TEXT,
            due TEXT NOT NULL,        -- YYYY-MM-DD
            due_time TEXT,            -- HH:MM
            priority TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    # new: device tokens for FCM
    conn.execute("""
        CREATE TABLE IF NOT EXISTS device_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()

# ---------------------- SCHEDULER ----------------------
scheduler = BackgroundScheduler(daemon=True)
# We'll start it after defining the job function to avoid race conditions
# (we'll call scheduler.start() at the end of setup)

def send_scheduled_fcm(reminder_id):
    """
    Job function run by APScheduler at reminder due datetime.
    Fetch reminder from DB, send FCM to saved device tokens, mark completed.
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone()
            if not row:
                print(f"[scheduler] Reminder id {reminder_id} not found in DB.")
                return
            if row["completed"]:
                print(f"[scheduler] Reminder id {reminder_id} already completed.")
                return

            # Build message
            task = row["task"]
            due = row["due"]
            due_time = row["due_time"] or ""
            priority = row["priority"] or ""

            # Fetch tokens from DB
            tokens_rows = conn.execute("SELECT token FROM device_tokens").fetchall()
            tokens = [r["token"] for r in tokens_rows]

            # Send FCM if tokens exist
            if tokens:
                try:
                    result = push_service.notify_multiple_devices(
                        registration_ids=tokens,
                        message_title="Reminder Due!",
                        message_body=f"{task} is due now ({due} {due_time}) Priority: {priority}"
                    )
                    print("[scheduler] FCM sent:", result)
                except Exception as e:
                    print("[scheduler] FCM send error:", e)
            else:
                print("[scheduler] No device tokens to notify.")

            # Mark reminder as completed in DB
            conn.execute("UPDATE reminders SET completed=1 WHERE id=?", (reminder_id,))
            conn.commit()

            # Also update in-memory list if present
            for r in reminders:
                # match by DB id stored in r.get('db_id') or fallback to matching fields
                if r.get('db_id') == reminder_id or (r.get('task') == task and r.get('due') == due and r.get('due_time') == due_time):
                    r['completed'] = True
                    # add history entry
                    history_entry = {
                        "action": "completed",
                        "reminder": r.copy(),
                        "timestamp": datetime.now().isoformat()
                    }
                    reminder_history.append(history_entry)
                    save_data()
                    break
    except Exception as ex:
        print("[scheduler] Exception in send_scheduled_fcm:", ex)

def schedule_job_for_reminder_dbrow(row):
    """
    Given a DB row (sqlite3.Row) from reminders table, schedule a job if due datetime is in future and not completed.
    """
    try:
        if row["completed"]:
            return
        due = row["due"]              # YYYY-MM-DD
        due_time = row["due_time"] or "00:00"
        dt_str = f"{due} {due_time}"
        due_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        if due_dt <= datetime.now():
            # If due time already passed, do not schedule (optionally could run immediately)
            return
        job_id = f"reminder_{row['id']}"
        # Use replace_existing to avoid duplicates
        scheduler.add_job(func=lambda rid=row['id']: send_scheduled_fcm(rid),
                          trigger="date",
                          run_date=due_dt,
                          id=job_id,
                          replace_existing=True)
        print(f"[scheduler] Scheduled reminder id={row['id']} at {due_dt.isoformat()}")
    except Exception as e:
        print("[scheduler] schedule_job_for_reminder_dbrow error:", e)

# load reminders from DB and schedule pending ones
def load_and_schedule_db_reminders():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM reminders WHERE completed=0").fetchall()
            for r in rows:
                # also keep in-memory list consistent: add if not present
                already = False
                for im in reminders:
                    if im.get('db_id') == r['id']:
                        already = True
                        break
                if not already:
                    reminder_obj = {
                        "task": r["task"],
                        "category": r["category"],
                        "due": r["due"],
                        "due_time": r["due_time"],
                        "priority": r["priority"],
                        "completed": bool(r["completed"]),
                        "created_at": r["created_at"],
                        "id": len(reminders),
                        "db_id": r["id"]
                    }
                    reminders.append(reminder_obj)
                # schedule job
                schedule_job_for_reminder_dbrow(r)
    except Exception as ex:
        print("[startup] load_and_schedule_db_reminders error:", ex)

# ---------------------- DASHBOARD ----------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------------------- CLASS ROUTES ----------------------
@app.route("/classes", methods=["GET"])
def classes():
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
        return redirect(url_for("classes"))

    return render_template("add_class.html")

@app.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        if not class_obj:
            flash("Class not found", "error")
            return redirect(url_for('classes'))

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
            return redirect(url_for('classes'))

    return render_template('edit_class.html', class_obj=class_obj)

@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    with get_db_connection() as conn:
        class_obj = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        if class_obj:
            conn.execute("DELETE FROM classes WHERE id=?", (class_id,))
            conn.commit()
            flash("Class deleted successfully!", "success")
    return redirect(url_for('classes'))

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
        due_dt = datetime.combine(due_date, due_time) if due_time else datetime.combine(due_date, datetime.min.time())

        if due_date == now.date() and (not due_time or now < due_dt):
            tasks.append(f"{t.task} (due today)")
        if due_time and 0 <= (now - due_dt).total_seconds() < 120:
            tasks.append(f"{t.task} (due now)")
        if due_time and (now - due_dt).total_seconds() >= 600:
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
        if not t.due_date or t.is_done:
            continue
        due_date = datetime.strptime(str(t.due_date), "%Y-%m-%d").date()
        due_time = datetime.strptime(t.due_time, "%H:%M").time() if t.due_time else None
        due_dt = datetime.combine(due_date, due_time) if due_time else datetime.combine(due_date, datetime.min.time())

        if due_time and 0 <= (now - due_dt).total_seconds() < 60:
            tasks.append(f"{t.task} (due now)")
        elif due_time and (now - due_dt).total_seconds() >= 600:
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

# Start the existing scheduler job for Todo check
if not scheduler.get_jobs():
    scheduler.add_job(check_and_notify, trigger="interval", minutes=1)
# Start the scheduler (will also be used for reminder jobs)
scheduler.start()

# After scheduler started, load DB reminders into memory and schedule
load_and_schedule_db_reminders()

# ---------------------- FILE UPLOADS ----------------------
@app.route("/dashboard/upload", methods=["POST"])
def upload_files():
    files = request.files.getlist("files[]")
    saved_files = []

    for f in files:
        if f.filename == "":
            continue
        filename = secure_filename(f.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(save_path)

        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO uploaded_files (filename, path)
                VALUES (?, ?)
            """, (filename, f"/uploads/{filename}"))
            conn.commit()

        saved_files.append(filename)

    return jsonify({"uploaded": saved_files})

@app.route("/dashboard/files")
def get_uploaded_files():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM uploaded_files").fetchall()
    files = [{"filename": r["filename"], "path": r["path"]} for r in rows]
    return jsonify(files)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/dashboard/delete_file", methods=["POST"])
def delete_file():
    data = request.get_json()
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    with get_db_connection() as conn:
        conn.execute("DELETE FROM uploaded_files WHERE filename=?", (filename,))
        conn.commit()

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return jsonify({"success": True})

@app.route("/dashboard/delete_all_files", methods=["POST"])
def delete_all_files():
    with get_db_connection() as conn:
        conn.execute("DELETE FROM uploaded_files")
        conn.commit()

    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))

    return jsonify({"success": True})

# ---------------------- CALENDAR ----------------------
@app.route('/calendar')
def calendar_view():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    cal_obj = cal.Calendar(firstweekday=6)
    month_days = cal_obj.monthdayscalendar(year, month)

    weeks = []
    today = datetime.now().date()

    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': '', 'current_month': False, 'is_today': False, 'events': []})
            else:
                day_date = datetime(year, month, day).date()
                week_data.append({
                    'day': day,
                    'current_month': True,
                    'is_today': (day_date == today),
                    'events': get_events_for_date(day_date)
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
    date_str = date.strftime("%Y-%m-%d")
    with get_db_connection() as conn:
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
            'color': '#ff8c66' if not todo.is_done else '#888888'
        })
    return events

@app.route('/todo_details/<int:todo_id>')
def todo_details(todo_id):
    todo = Todo.get_by_id(todo_id)
    if not todo:
        flash("Task not found", "error")
        return redirect(url_for('calendar_view'))
    return render_template('todo_details.html', todo=todo)

# ---------------------- HOME ----------------------
@app.route('/')
def home():
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    current_day = datetime.now().strftime("%A")

    with get_db_connection() as conn:
        today_classes = conn.execute(
            "SELECT * FROM classes WHERE day = ? ORDER BY start_time",
            (current_day,)
        ).fetchall()

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_tasks = []
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE due_date = ? ORDER BY due_time",
            (today_str,)
        ).fetchall()
        today_tasks = [Todo(**dict(row)) for row in rows]

    completed_tasks = sum(1 for t in today_tasks if t.is_done)
    total_tasks = len(today_tasks)
    return render_template('home.html',
                           current_date=current_date,
                           today_classes=today_classes,
                           today_tasks=today_tasks,
                           completed_tasks=completed_tasks,
                           total_tasks=total_tasks)

# ---------------------- JOURNAL ROUTES ----------------------
with get_db_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            mood INTEGER NOT NULL,
            energy INTEGER NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()


@app.route("/journal", methods=["GET", "POST"])
def journal():
    with get_db_connection() as conn:
        if request.method == "POST":
            entry_date = request.form["entry_date"]
            mood = request.form["mood"]
            energy = request.form["energy"]
            notes = request.form.get("notes", "")

            conn.execute(
                "INSERT INTO journal (entry_date, mood, energy, notes) VALUES (?, ?, ?, ?)",
                (entry_date, mood, energy, notes),
            )
            conn.commit()
            flash("Journal entry saved!")
            return redirect(url_for("journal"))

        # ✅ Include ID so the template can access entry['id']
        entries = conn.execute(
            "SELECT id, entry_date, mood, energy, notes FROM journal ORDER BY entry_date DESC"
        ).fetchall()

    return render_template(
        "mood_journal.html",  # ✅ your filename here
        entries=entries,
        today=date.today().strftime("%Y-%m-%d"),
    )


@app.route('/delete_journal/<int:id>', methods=['POST'])
def delete_journal(id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM journal WHERE id = ?", (id,))
        conn.commit()
    flash("Journal entry deleted successfully!", "success")
    return redirect(url_for('journal'))  # ✅ fixed


@app.route('/edit_journal/<int:id>', methods=['GET', 'POST'])
def edit_journal(id):
    with get_db_connection() as conn:
        journal = conn.execute("SELECT * FROM journal WHERE id = ?", (id,)).fetchone()

    if not journal:
        flash("Journal entry not found.", "danger")
        return redirect(url_for('journal'))

    if request.method == 'POST':
        new_date = request.form['entry_date']
        new_mood = request.form['mood']
        new_energy = request.form['energy']
        new_notes = request.form['notes']

        with get_db_connection() as conn:
            conn.execute("""
                UPDATE journal 
                SET entry_date = ?, mood = ?, energy = ?, notes = ?
                WHERE id = ?
            """, (new_date, new_mood, new_energy, new_notes, id))
            conn.commit()

        flash("Journal updated successfully!", "success")
        return redirect(url_for('journal'))

    return render_template('edit_journal.html', journal=journal)

# ---------------------- REMINDER PAGE ----------------------
@app.route("/reminder_page")
def reminder_page():
    return render_template("reminder.html")

# ---------------------- REMINDERS API ----------------------
@app.route("/reminders", methods=["GET"])
def get_reminders():
    # Ensure all reminders have completed field
    for reminder in reminders:
        if "completed" not in reminder:
            reminder["completed"] = False
    return jsonify(reminders), 200

@app.route("/reminders", methods=["POST"])
def add_reminder():
    data = request.get_json()
    required_fields = ["task", "category", "due"]

    # check the field are complete
    if all(field in data and data[field] for field in required_fields):
        reminder = {
            "task": data["task"].strip(),
            "category": data["category"],
            "due": data["due"],
            "due_time": data.get("due_time", "09:00"),
            "priority": data.get("priority", "medium"),
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "id": len(reminders)
        }

        # Save into in-memory list (keeps compatibility with existing frontend)
        reminders.append(reminder)

        # Persist into DB and schedule job
        try:
            with get_db_connection() as conn:
                cur = conn.execute("""
                    INSERT INTO reminders (task, category, due, due_time, priority, completed, created_at)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                """, (reminder["task"], reminder["category"], reminder["due"], reminder["due_time"], reminder["priority"], reminder["created_at"]))
                conn.commit()
                db_id = cur.lastrowid
                # attach db id to in-memory reminder for future reference
                reminder["db_id"] = db_id

                # Schedule the job (if due datetime in future)
                try:
                    due_dt = datetime.strptime(f"{reminder['due']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
                    if due_dt > datetime.now():
                        scheduler.add_job(func=lambda rid=db_id: send_scheduled_fcm(rid),
                                          trigger="date",
                                          run_date=due_dt,
                                          id=f"reminder_{db_id}",
                                          replace_existing=True)
                        print(f"[add_reminder] scheduled reminder db_id={db_id} at {due_dt.isoformat()}")
                    else:
                        print(f"[add_reminder] due datetime {due_dt} is in the past; not scheduling job.")
                except Exception as e:
                    print("[add_reminder] scheduling error:", e)
        except Exception as ex:
            print("[add_reminder] DB insert error:", ex)

        # Add to history
        history_entry = {
            "action": "created",
            "reminder": reminder.copy(),
            "timestamp": datetime.now().isoformat()
        }
        reminder_history.append(history_entry)

        save_data()

        # Don't send immediate FCM here; scheduling will handle send at due time.
        return jsonify({
            "message": "Reminder added successfully",
            "reminders": reminders
        }), 201
    else:
        return jsonify({
            "error": "Data incomplete"
            }), 400

# Save device token (FCM) from frontend
@app.route("/save_token", methods=["POST"])
def save_token():
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"error": "No token provided"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO device_tokens (token) VALUES (?)", (token,))
            conn.commit()
    except Exception as e:
        print("[save_token] error:", e)
        return jsonify({"error": "DB error"}), 500
    return jsonify({"success": True}), 200

# delete reminder
@app.route("/reminders/<int:reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    # Find the reminder by its id field
    reminder_to_delete = next((r for r in reminders if r["id"] == reminder_id), None)

    if reminder_to_delete:
        reminders.remove(reminder_to_delete)

        db_id = reminder_to_delete.get("db_id")
        if db_id:
            try:
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM reminders WHERE id=?", (db_id,))
                    conn.commit()
                    # remove scheduled job if exists
                    try:
                        scheduler.remove_job(f"reminder_{db_id}")
                    except Exception:
                        pass
            except Exception as e:
                print("[delete_reminder] DB delete error:", e)

        # Add to history
        history_entry = {
            "action": "deleted",
            "reminder": reminder_to_delete,
            "timestamp": datetime.now().isoformat()
        }
        reminder_history.append(history_entry)

        save_data()
        return jsonify({
            "message": f"Reminder deleted: {reminder_to_delete['task']}",
            "reminders": reminders
        }), 200
    else:
        return jsonify({
            "error": "Cannot find the reminder"
        }), 404

# get reminder history
@app.route("/history", methods=["GET"])
def get_history():
    return jsonify(reminder_history), 200

# check upcoming reminders for notifications
@app.route("/upcoming", methods=["GET"])
def get_upcoming():
    upcoming = []
    today = datetime.now().date()

    for reminder in reminders:
        due_date = datetime.strptime(reminder["due"], "%Y-%m-%d").date()
        days_left = (due_date - today).days

        if 0 <= days_left <= 3:  # Due within 3 days
            upcoming.append({
                **reminder,
                "days_left": days_left,
                "urgent": days_left == 0
            })

    return jsonify(upcoming), 200

# Notes API endpoints
@app.route("/notes", methods=["GET"])
def get_notes():
    return jsonify(notes), 200

@app.route("/notes", methods=["POST"])
def add_note():
    data = request.get_json()
    if data and "content" in data and data["content"].strip():
        note = {
            "content": data["content"].strip(),
            "created_at": datetime.now().isoformat(),
            "id": len(notes)
        }
        notes.append(note)
        save_data()
        return jsonify({
            "message": "Note added successfully",
            "notes": notes
        }), 201
    else:
        return jsonify({
            "error": "Note content is required"
        }), 400

@app.route("/notes/<int:index>", methods=["DELETE"])
def delete_note(index):
    if 0 <= index < len(notes):
        deleted = notes.pop(index)
        save_data()
        return jsonify({
            "message": f"Note deleted: {deleted['content']}",
            "notes": notes
        }), 200
    else:
        return jsonify({"error": "Note not found"}), 404 
    
    
    # ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    app.run(debug=True)


# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    app.run(debug=True)


@app.route("/reminders/<int:id>/complete", methods=["PUT"])
def complete_reminder(id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE reminders SET is_done = 1 WHERE id = ?", (id,))
        if cur.rowcount == 0:
            return jsonify({"error": "Reminder not found"}), 404
        conn.commit()
    return jsonify({"message": "Reminder marked completed"}), 200
