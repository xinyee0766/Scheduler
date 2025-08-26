<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Reminder Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background-image:url(background.jpg); }
    form { background: #fff; padding: 24px; border-radius: 8px; max-width: 400px; margin: auto; box-shadow: 0 2px 8px #ddd; }
    label { display: block; margin-top: 12px; font-weight: bold; }
    input { width: 100%; padding: 8px; margin-top: 4px; margin-bottom: 8px; border-radius: 4px; border: 1px solid #ccc; }
    button { background: #28a745; color: #fff; padding: 10px 18px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
    button:hover { background: #218838; }

    #dashboard { max-width: 600px; margin: 40px auto; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #fff; box-shadow: 0 2px 8px #ddd; }
    th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
    th { background: #f1f1f1; }
    .delete-btn { background: #dc3545; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
    .delete-btn:hover { background: #c82333; }
  </style>
</head>
<body>
  <form id="reminderForm">
    <h2>Add Reminder</h2>
    <label for="task">Task Name</label>
    <input type="text" id="task" placeholder="Exm:Assignment" required>

    <label for="subject">Subject</label>
    <input type="text" id="subject" placeholder="it" required>

    <label for="due">Due Date</label>
    <input type="date" id="due" name="due" required>

    <button type="submit">Add Reminder</button>
  </form>

  <div id="dashboard">
    <h2>My Reminders</h2>
    <table>
      <thead>
        <tr>
          <th>Task</th>
          <th>Subject</th>
          <th>Due Date</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="reminderList"></tbody>
    </table>
  </div>

  <script>
    // save reminders
    let reminders = JSON.parse(localStorage.getItem("reminders")) || [];
    let reminderList = document.getElementById("reminderList");

    // show reminder
    function showReminders() {
      reminderList.innerHTML = "";
      for (let i = 0; i < reminders.length; i++) {
        let r = reminders[i];
        let row = "<tr>" +
          "<td>" + r.task + "</td>" +
          "<td>" + r.subject + "</td>" +
          "<td>" + r.due + "</td>" +
          "<td><button class='delete-btn' onclick='deleteReminder(" + i + ")'>Delete</button></td>" +
          "</tr>";
        reminderList.innerHTML += row;
      }
    }

    // add reminder
    document.getElementById("reminderForm").addEventListener("submit", function(e) {
      e.preventDefault();
      let task = document.getElementById("task").value;
      let subject = document.getElementById("subject").value;
      let due = document.getElementById("due").value;

      reminders.push({ task: task, subject: subject, due: due });
      localStorage.setItem("reminders", JSON.stringify(reminders));

      showReminders();
      this.reset();
    });

    // de;ete reminder
    function deleteReminder(index) {
      reminders.splice(index, 1);
      localStorage.setItem("reminders", JSON.stringify(reminders));
      showReminders();
    }

    showReminders();
  </script>
</body>
</html>
