from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

# save reminder
reminders = []
# save reminder history
reminder_history = []
# save notes
notes = []

# Load data from file if exists
def load_data():
    global reminders, reminder_history, notes
    if os.path.exists('reminders.json'):
        with open('reminders.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            reminders = data.get('reminders', [])
            reminder_history = data.get('history', [])
            notes = data.get('notes', [])

# Save data to file
def save_data():
    data = {
        'reminders': reminders,
        'history': reminder_history,
        'notes': notes
    }
    with open('reminders.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Load data on startup
load_data()

# get reminder
@app.route("/reminders", methods=["GET"])
def get_reminders():
    # Ensure all reminders have completed field
    for reminder in reminders:
        if "completed" not in reminder:
            reminder["completed"] = False
    return jsonify(reminders), 200

# add new reminder
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
        reminders.append(reminder)
        
        # Add to history
        history_entry = {
            "action": "created",
            "reminder": reminder.copy(),
            "timestamp": datetime.now().isoformat()
        }
        reminder_history.append(history_entry)
        
        save_data()
        return jsonify({
            "message": "Reminder added successfully",
            "reminders": reminders
        }), 201
    else:
        return jsonify({
            "error": "Data incomplete"
        }), 400

# delete reminder
@app.route("/reminders/<int:index>", methods=["DELETE"])
def delete_reminder(index):
    if 0 <= index < len(reminders):
        deleted = reminders.pop(index)
        
        # Add to history
        history_entry = {
            "action": "deleted",
            "reminder": deleted,
            "timestamp": datetime.now().isoformat()
        }
        reminder_history.append(history_entry)
        
        save_data()
        return jsonify({
            "message": f"Reminder deleted: {deleted['task']}",
            "reminders": reminders
        }), 200
    else:
        return jsonify({
            "error": "Cannot find the reminders"
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
        
        if 0 <= days_le
