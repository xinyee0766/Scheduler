<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Reminder Dashboard</title>
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      margin: 40px;
      background: linear-gradient(to right, #e0f7fa, #fce4ec);
    }
    form {
      background: #ffffff;
      padding: 24px;
      border-radius: 12px;
      max-width: 400px;
      margin: auto;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    h2 {
      text-align: center;
      color: #333;
    }
    label {
      display: block;
      margin-top: 12px;
      font-weight: bold;
      color: #555;
    }
    input {
      width: 100%;
      padding: 10px;
      margin-top: 4px;
      margin-bottom: 12px;
      border-radius: 6px;
      border: 1px solid #ccc;
      box-sizing: border-box;
    }
    button {
      background: #007bff;
      color: #fff;
      padding: 10px 18px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
      width: 100%;
    }
    button:hover {
      background: #0056b3;
    }
    #dashboard {
      max-width: 600px;
      margin: 40px auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      background: #fff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    th, td {
      padding: 12px;
      border: 1px solid #ddd;
      text-align: left;
    }
    th {
      background: #f1f1f1;
    }
    .delete-btn {
      background: #dc3545;
      color: #fff;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
    }
    .delete-btn:hover {
      background: #c82333;
    }
  </style>
</head>
<body>
  <form id="reminderForm">
    <h2>Add Reminder</h2>
    <label for="task">Reminder Name</label>
    <input type="text" id="task" placeholder="Exm:assignment" required>

    <label for="subject">Subject</label>
    <input type="text" id="subject" placeholder="Exm:Math" required>

    <label for="due">Deadline</label>
    <input type="date" id="due" required>

    <button type="submit">Add Reminder</button>
  </form>

  <div id="dashboard">
    <h2>My Reminder List</h2>
    <table>
      <thead>
        <tr>
          <th>Reminder Name</th>
          <th>Subject</th>
          <th>Deadline</th>
          <th>Operate</th>
        </tr>
      </thead>
      <tbody id="reminderList"></tbody>
    </table>
  </div>

<script>
const reminderList = document.getElementById("reminderList");
const API_URL = "http://localhost:5000/reminders"; // makesure same with flask

//show reminder list
async function showReminders() {
  try {
    const res = await fetch(API_URL);
    const reminders = await res.json();
    reminderList.innerHTML = "";
    reminders.forEach((r, i) => {
      reminderList.innerHTML += `
        <tr>
          <td>${r.task}</td>
          <td>${r.subject}</td>
          <td>${r.due}</td>
          <td><button class="delete-btn" onclick="deleteReminder(${i})">delete</button></td>
        </tr>
      `;
    });
  } catch (err) {
    console.error("Cannot get the reminder list：", err);
  }
}

// add reminder
document.getElementById("reminderForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  const task = document.getElementById("task").value.trim();
  const subject = document.getElementById("subject").value.trim();
  const due = document.getElementById("due").value;

  if (!task || !subject || !due) {
    alert("please write the task");
    return;
  }

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task, subject, due })
    });
    const result = await res.json();
    console.log("Successful：", result);
    showReminders();
    this.reset();
  } catch (err) {
    console.error("Fail：", err);
  }
});

// delete reminder
async function deleteReminder(index) {
  try {
    const res = await fetch(`${API_URL}/${index}`, {
      method: "DELETE"
    });
    const result = await res.json();
    console.log("delete successfully：", result);
    showReminders();
  } catch (err) {
    console.error("delete failed：", err);
  }
}

showReminders();
</script>
</body>
</html>
