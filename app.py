from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from models import Todo, Class, init_db
from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
import json

# ---------------------- APP SETUP ----------------------
app = Flask(__name__)
app.secret_key = "xinyee0766"

DB_NAME = os.path.join(os.path.dirname(__file__), 'classes.db')
SUBSCRIPTIONS = []

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
init_db()

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

# ---------------------- TO-DO ROUTES ----------------------
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
        task = request.form["task"]
        due_date = request.form["due_date"]
        due_time = request.form.get("due_time")
        todo = Todo(task=task, due_date=due_date, due_time=due_time)
        todo.save()
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
        todo.task = request.form["task"]
        todo.due_date = request.form["due_date"]
        todo.due_time = request.form.get("due_time")
        todo.is_done = int("is_done" in request.form)
        todo.save()
        flash("Task updated successfully!", "success")
        return redirect(url_for("todos"))
    return render_template("edit_todo.html", todo=todo)

@app.route("/todos/delete/<int:todo_id>", methods=["POST"])
def delete_todo(todo_id):
    todo = Todo.get_by_id(todo_id)
    if todo:
        todo.delete()
        flash("Task deleted successfully!", "success")
    return redirect(url_for("todos"))

@app.route("/todos/check")
def check_todos():
    due_today = Todo.get_due_today()
    return {"tasks": [t.task for t in due_today]}

# ---------------------- PUSH NOTIFICATIONS ----------------------
@app.route("/subscribe", methods=["POST"])
def subscribe():
    subscription_info = request.get_json()
    if subscription_info not in SUBSCRIPTIONS:
        SUBSCRIPTIONS.append(subscription_info)
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

# ---------------------- TEST PUSH ROUTE ----------------------
@app.route("/test_push")
def test_push():
    if not SUBSCRIPTIONS:
        return "No subscriptions yet!"
    
    for sub in SUBSCRIPTIONS:
        send_push_notification(sub, "Test Push", "This is a test notification")
    
    return "Push sent!"

notified_log = set()

def notify_due_tasks():
    now = datetime.now()
    due_today = Todo.get_due_today()

    for task in due_today:
        task_id = getattr(task, "id", task.task)

        # Start-of-day notification
        if now.hour == 0 and now.minute == 0:
            key = (task_id, "start")
            if key not in notified_log:
                title = "Task Due Today"
                body = f"{task.task} is due today!"
                for sub in SUBSCRIPTIONS:
                    send_push_notification(sub, title, body)
                notified_log.add(key)

        if task.due_time:
            due_dt = datetime.combine(task.due_date, datetime.strptime(task.due_time, "%H:%M").time())
            diff_seconds = (now - due_dt).total_seconds()

            # Exact due time
            if 0 <= diff_seconds < 60:
                key = (task_id, "due")
                if key not in notified_log:
                    title = "Task Due Now"
                    body = f"{task.task} is due!"
                    for sub in SUBSCRIPTIONS:
                        send_push_notification(sub, title, body)
                    notified_log.add(key)

            # 10 minutes overdue
            elif 600 <= diff_seconds < 660:
                key = (task_id, "overdue10")
                if key not in notified_log:
                    title = "Task Overdue"
                    body = f"{task.task} is overdue by 10 minutes!"
                    for sub in SUBSCRIPTIONS:
                        send_push_notification(sub, title, body)
                    notified_log.add(key)

@app.context_processor
def inject_vapid_key():
    return dict(VAPID_PUBLIC_KEY=VAPID_PUBLIC_KEY)

# ---------------------- BACKGROUND SCHEDULER ----------------------
scheduler = BackgroundScheduler(daemon=True)
if not scheduler.get_jobs():
    scheduler.add_job(func=notify_due_tasks, trigger="interval", minutes=1)
scheduler.start()

# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
