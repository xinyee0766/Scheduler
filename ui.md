<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Reminder Dashboard</title>
  <style>
    :root {
      --primary-bg: linear-gradient(to right, #e0f7fa, #fce4ec);
      --secondary-bg: #ffffff;
      --text-color: #333;
      --border-color: #ddd;
    }
    
    body {
      font-family: 'Segoe UI', sans-serif;
      margin: 40px;
      background: var(--primary-bg);
      color: var(--text-color);
      transition: all 0.3s ease;
    }
    
    .theme-controls {
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--secondary-bg);
      padding: 15px;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      z-index: 1000;
    }
    
    .theme-controls h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
    }
    
    .color-picker {
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
    }
    
    .color-option {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      border: 2px solid #fff;
      cursor: pointer;
      transition: transform 0.2s;
    }
    
    .color-option:hover {
      transform: scale(1.1);
    }
    
    .notification-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
    }
    
    .notification-toggle input[type="checkbox"] {
      width: auto;
      margin: 0;
    }
    form {
      background: var(--secondary-bg);
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
      background: var(--secondary-bg);
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    th, td {
      padding: 12px;
      border: 1px solid var(--border-color);
      text-align: left;
    }
    th {
      background: #f1f1f1;
    }
    
    .urgent {
      background-color: #ffebee !important;
      border-left: 4px solid #f44336;
    }
    
    .due-soon {
      background-color: #fff3e0 !important;
      border-left: 4px solid #ff9800;
    }
    
    .tabs {
      display: flex;
      margin-bottom: 20px;
      background: var(--secondary-bg);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .tab {
      flex: 1;
      padding: 12px;
      text-align: center;
      cursor: pointer;
      background: #f5f5f5;
      border: none;
      transition: background 0.3s;
    }
    
    .tab.active {
      background: #007bff;
      color: white;
    }
    
    .tab-content {
      display: none;
    }
    
    .tab-content.active {
      display: block;
    }
    
    .history-item {
      background: var(--secondary-bg);
      padding: 12px;
      margin: 8px 0;
      border-radius: 6px;
      border-left: 4px solid #007bff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .history-item.deleted {
      border-left-color: #dc3545;
    }
    
    .history-time {
      font-size: 12px;
      color: #666;
      margin-top: 4px;
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
  <!-- Theme Controls -->
  <div class="theme-controls">
    <h4>主题设置</h4>
    <div class="color-picker">
      <div class="color-option" data-theme="default" style="background: linear-gradient(to right, #e0f7fa, #fce4ec);"></div>
      <div class="color-option" data-theme="dark" style="background: linear-gradient(to right, #2c3e50, #34495e);"></div>
      <div class="color-option" data-theme="green" style="background: linear-gradient(to right, #e8f5e8, #f0f8f0);"></div>
      <div class="color-option" data-theme="purple" style="background: linear-gradient(to right, #f3e5f5, #e1bee7);"></div>
      <div class="color-option" data-theme="orange" style="background: linear-gradient(to right, #fff3e0, #ffe0b2);"></div>
    </div>
    <div class="notification-toggle">
      <input type="checkbox" id="notificationToggle">
      <label for="notificationToggle">启用通知</label>
    </div>
  </div>

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
    <h2>My Reminder Dashboard</h2>
    
    <!-- Tabs -->
    <div class="tabs">
      <button class="tab active" data-tab="current">当前提醒</button>
      <button class="tab" data-tab="history">历史记录</button>
    </div>
    
    <!-- Current Reminders Tab -->
    <div id="current" class="tab-content active">
      <table>
        <thead>
          <tr>
            <th>Reminder Name</th>
            <th>Subject</th>
            <th>Deadline</th>
            <th>Status</th>
            <th>Operate</th>
          </tr>
        </thead>
        <tbody id="reminderList"></tbody>
      </table>
    </div>
    
    <!-- History Tab -->
    <div id="history" class="tab-content">
      <div id="historyList"></div>
    </div>
  </div>

<script>
const reminderList = document.getElementById("reminderList");
const historyList = document.getElementById("historyList");
const API_URL = "http://localhost:5000"; // makesure same with flask

// Theme management
const themes = {
  default: {
    primary: 'linear-gradient(to right, #e0f7fa, #fce4ec)',
    secondary: '#ffffff',
    text: '#333',
    border: '#ddd'
  },
  dark: {
    primary: 'linear-gradient(to right, #2c3e50, #34495e)',
    secondary: '#34495e',
    text: '#ecf0f1',
    border: '#4a5f7a'
  },
  green: {
    primary: 'linear-gradient(to right, #e8f5e8, #f0f8f0)',
    secondary: '#ffffff',
    text: '#2e7d32',
    border: '#c8e6c9'
  },
  purple: {
    primary: 'linear-gradient(to right, #f3e5f5, #e1bee7)',
    secondary: '#ffffff',
    text: '#7b1fa2',
    border: '#ce93d8'
  },
  orange: {
    primary: 'linear-gradient(to right, #fff3e0, #ffe0b2)',
    secondary: '#ffffff',
    text: '#ef6c00',
    border: '#ffcc02'
  }
};

// Apply theme
function applyTheme(themeName) {
  const theme = themes[themeName];
  document.documentElement.style.setProperty('--primary-bg', theme.primary);
  document.documentElement.style.setProperty('--secondary-bg', theme.secondary);
  document.documentElement.style.setProperty('--text-color', theme.text);
  document.documentElement.style.setProperty('--border-color', theme.border);
  localStorage.setItem('selectedTheme', themeName);
}

// Load saved theme
const savedTheme = localStorage.getItem('selectedTheme') || 'default';
applyTheme(savedTheme);

// Theme controls
document.querySelectorAll('.color-option').forEach(option => {
  option.addEventListener('click', () => {
    const theme = option.dataset.theme;
    applyTheme(theme);
  });
});

// Notification permission and management
let notificationEnabled = localStorage.getItem('notificationEnabled') === 'true';
document.getElementById('notificationToggle').checked = notificationEnabled;

document.getElementById('notificationToggle').addEventListener('change', async (e) => {
  notificationEnabled = e.target.checked;
  localStorage.setItem('notificationEnabled', notificationEnabled);
  
  if (notificationEnabled && Notification.permission === 'default') {
    await Notification.requestPermission();
  }
});

// Tab management
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove active class from all tabs and contents
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    tab.classList.add('active');
    const tabId = tab.dataset.tab;
    document.getElementById(tabId).classList.add('active');
    
    // Load content if history tab
    if (tabId === 'history') {
      showHistory();
    }
  });
});

// Show reminder list with status
async function showReminders() {
  try {
    const res = await fetch(`${API_URL}/reminders`);
    const reminders = await res.json();
    reminderList.innerHTML = "";
    
    reminders.forEach((r, i) => {
      const dueDate = new Date(r.due);
      const today = new Date();
      const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
      
      let statusClass = '';
      let statusText = '';
      
      if (daysLeft < 0) {
        statusClass = 'urgent';
        statusText = '已过期';
      } else if (daysLeft === 0) {
        statusClass = 'urgent';
        statusText = '今天到期';
      } else if (daysLeft <= 3) {
        statusClass = 'due-soon';
        statusText = `${daysLeft}天后到期`;
      } else {
        statusText = `${daysLeft}天后到期`;
      }
      
      reminderList.innerHTML += `
        <tr class="${statusClass}">
          <td>${r.task}</td>
          <td>${r.subject}</td>
          <td>${r.due}</td>
          <td>${statusText}</td>
          <td><button class="delete-btn" onclick="deleteReminder(${i})">delete</button></td>
        </tr>
      `;
    });
    
    // Check for notifications
    if (notificationEnabled) {
      checkNotifications();
    }
  } catch (err) {
    console.error("Cannot get the reminder list：", err);
  }
}

// Show history
async function showHistory() {
  try {
    const res = await fetch(`${API_URL}/history`);
    const history = await res.json();
    historyList.innerHTML = "";
    
    if (history.length === 0) {
      historyList.innerHTML = '<p style="text-align: center; color: #666;">暂无历史记录</p>';
      return;
    }
    
    // Sort by timestamp (newest first)
    history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    history.forEach(item => {
      const time = new Date(item.timestamp).toLocaleString('zh-CN');
      const actionText = item.action === 'created' ? '创建了提醒' : '删除了提醒';
      const actionClass = item.action === 'created' ? '' : 'deleted';
      
      historyList.innerHTML += `
        <div class="history-item ${actionClass}">
          <strong>${actionText}: ${item.reminder.task}</strong>
          <div>科目: ${item.reminder.subject}</div>
          <div>截止日期: ${item.reminder.due}</div>
          <div class="history-time">${time}</div>
        </div>
      `;
    });
  } catch (err) {
    console.error("Cannot get history：", err);
    historyList.innerHTML = '<p style="text-align: center; color: #f44336;">加载历史记录失败</p>';
  }
}

// Check notifications
async function checkNotifications() {
  if (!notificationEnabled || Notification.permission !== 'granted') {
    return;
  }
  
  try {
    const res = await fetch(`${API_URL}/upcoming`);
    const upcoming = await res.json();
    
    upcoming.forEach(reminder => {
      if (reminder.urgent) {
        new Notification(`紧急提醒: ${reminder.task}`, {
          body: `科目: ${reminder.subject} - 今天到期！`,
          icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="red"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
          tag: `urgent-${reminder.id}`
        });
      } else if (reminder.days_left <= 3) {
        new Notification(`提醒: ${reminder.task}`, {
          body: `科目: ${reminder.subject} - ${reminder.days_left}天后到期`,
          icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="orange"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
          tag: `upcoming-${reminder.id}`
        });
      }
    });
  } catch (err) {
    console.error("Notification check failed：", err);
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
    const res = await fetch(`${API_URL}/reminders`, {
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
    const res = await fetch(`${API_URL}/reminders/${index}`, {
      method: "DELETE"
    });
    const result = await res.json();
    console.log("delete successfully：", result);
    showReminders();
  } catch (err) {
    console.error("delete failed：", err);
  }
}

// Initialize
showReminders();

// Check notifications every 5 minutes
setInterval(() => {
  if (notificationEnabled) {
    checkNotifications();
  }
}, 5 * 60 * 1000);
</script>
</body>
</html>
