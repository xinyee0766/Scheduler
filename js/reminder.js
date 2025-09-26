// ================== Tabs ==================
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
  });
});

// ================== Load Reminders from DB ==================
async function loadReminders() {
  try {
    const res = await fetch("/reminders");
    const reminders = await res.json();
    const tbody = document.getElementById("reminderList");
    tbody.innerHTML = "";
    
    // Filter out completed reminders - they should only show in history
    const activeReminders = reminders.filter(r => !r.completed);
    
    if (activeReminders.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #888;">No active reminders. Add one above!</td></tr>';
      return;
    }
    
    activeReminders.forEach(r => {
      const priorityClass = r.priority ? `priority-${r.priority}` : "";
      
      const row = `<tr data-id="${r.id}" class="pending ${priorityClass}">
        <td>${r.task}</td>
        <td><span class="category-badge">${r.category}</span></td>
        <td>${formatDate(r.due)}</td>
        <td>${r.due_time || "All day"}</td>
        <td><span class="priority-badge priority-${r.priority}">${r.priority}</span></td>
        <td><span class="status-badge pending">Pending</span></td>
        <td>
          <button class="btn-complete" onclick="completeReminder(this)">
            Mark Done
          </button>
          <button class="btn-delete" onclick="deleteReminder(this)">Delete</button>
        </td>
      </tr>`;
      tbody.insertAdjacentHTML("beforeend", row);
    });
    
    updateStats();
  } catch (error) {
    console.error("Error loading reminders:", error);
  }
}

// Format date for display
function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString();
}

// Update statistics
async function updateStats() {
  try {
    const res = await fetch("/reminders");
    const reminders = await res.json();
    
    const total = reminders.length;
    const completed = reminders.filter(r => r.completed).length;
    const upcoming = reminders.filter(r => {
      if (r.completed) return false;
      const dueDate = new Date(r.due);
      const today = new Date();
      const diffTime = dueDate - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays >= 0 && diffDays <= 3;
    }).length;
    
    document.getElementById("totalReminders").textContent = total;
    document.getElementById("completedCount").textContent = completed;
    document.getElementById("upcomingCount").textContent = upcoming;
    
    // Load notes count
    const notesRes = await fetch("/notes");
    const notes = await notesRes.json();
    document.getElementById("notesCount").textContent = notes.length;
  } catch (error) {
    console.error("Error updating stats:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadReminders();
  loadHistory();
  loadNotes();
});

// ================== Add Reminder ==================
document.getElementById("reminderForm").addEventListener("submit", async e => {
  e.preventDefault();
  
  const task = document.getElementById("task").value.trim();
  const category = document.getElementById("category").value;
  const due = document.getElementById("due").value;
  const time = document.getElementById("due_time").value;
  const priority = document.getElementById("priority").value;

  if (!task || !category || !due) {
    alert("Please fill in all required fields!");
    return;
  }

  try {
    const response = await fetch("/reminders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task, category, due, due_time: time, priority })
    });

    if (response.ok) {
      e.target.reset();
      loadReminders();
      showNotification("Reminder added successfully!", "success");
    } else {
      throw new Error("Failed to add reminder");
    }
  } catch (error) {
    console.error("Error adding reminder:", error);
    showNotification("Failed to add reminder. Please try again.", "error");
  }
});

// ================== Complete Reminder ==================
async function completeReminder(btn) {
  const row = btn.closest("tr");
  const id = row.dataset.id;
  
  try {
    const response = await fetch(`/reminders/${id}/complete`, { method: "PUT" });
    if (response.ok) {
      loadReminders();
      showNotification("Reminder marked as completed!", "success");
    } else {
      throw new Error("Failed to complete reminder");
    }
  } catch (error) {
    console.error("Error completing reminder:", error);
    showNotification("Failed to complete reminder. Please try again.", "error");
  }
}

// ================== Delete Reminder ==================
async function deleteReminder(btn) {
  if (!confirm("Are you sure you want to delete this reminder?")) {
    return;
  }
  
  const row = btn.closest("tr");
  const id = row.dataset.id;
  
  try {
    const response = await fetch(`/reminders/${id}`, { method: "DELETE" });
    if (response.ok) {
      loadReminders();
      showNotification("Reminder deleted successfully!", "success");
    } else {
      throw new Error("Failed to delete reminder");
    }
  } catch (error) {
    console.error("Error deleting reminder:", error);
    showNotification("Failed to delete reminder. Please try again.", "error");
  }
}

// ================== Notes ==================
async function addNote() {
  const content = document.getElementById("noteContent").value.trim();
  if (!content) return;
  
  try {
    const response = await fetch("/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });
    
    if (response.ok) {
      document.getElementById("noteContent").value = "";
      loadNotes();
      showNotification("Note added successfully!", "success");
    } else {
      throw new Error("Failed to add note");
    }
  } catch (error) {
    console.error("Error adding note:", error);
    showNotification("Failed to add note. Please try again.", "error");
  }
}

// Load notes from server
async function loadNotes() {
  try {
    const response = await fetch("/notes");
    const notes = await response.json();
    const notesList = document.getElementById("notesList");
    notesList.innerHTML = "";
    
    if (notes.length === 0) {
      notesList.innerHTML = '<p style="color: #888; text-align: center;">No notes yet. Add one above!</p>';
      return;
    }
    
    notes.forEach((note, index) => {
      const noteDiv = document.createElement("div");
      noteDiv.className = "note-item";
      noteDiv.innerHTML = `
        <div class="note-content">${note.content}</div>
        <div class="note-meta">
          <span class="note-date">${new Date(note.created_at).toLocaleString()}</span>
          <button class="btn-delete-note" onclick="deleteNote(${index})">Delete</button>
        </div>
      `;
      notesList.appendChild(noteDiv);
    });
  } catch (error) {
    console.error("Error loading notes:", error);
  }
}

// Delete note
async function deleteNote(index) {
  if (!confirm("Are you sure you want to delete this note?")) {
    return;
  }
  
  try {
    const response = await fetch(`/notes/${index}`, { method: "DELETE" });
    if (response.ok) {
      loadNotes();
      showNotification("Note deleted successfully!", "success");
    } else {
      throw new Error("Failed to delete note");
    }
  } catch (error) {
    console.error("Error deleting note:", error);
    showNotification("Failed to delete note. Please try again.", "error");
  }
}

// ================== History ==================
async function loadHistory() {
  try {
    // Load both history entries and completed reminders
    const [historyResponse, remindersResponse] = await Promise.all([
      fetch("/history"),
      fetch("/reminders")
    ]);
    
    const history = await historyResponse.json();
    const reminders = await remindersResponse.json();
    const historyList = document.getElementById("historyList");
    historyList.innerHTML = "";
    
    // Filter completed reminders
    const completedReminders = reminders.filter(r => r.completed);
    
    if (history.length === 0 && completedReminders.length === 0) {
      historyList.innerHTML = '<p style="color: #888; text-align: center;">No history yet.</p>';
      return;
    }
    
    // Add completed reminders to history
    completedReminders.forEach(reminder => {
      const historyDiv = document.createElement("div");
      historyDiv.className = "history-item completed-reminder";
      historyDiv.innerHTML = `
        <div class="history-action">Completed</div>
        <div class="history-task">${reminder.task}</div>
        <div class="history-details">
          <span class="category-badge">${reminder.category}</span>
          <span class="priority-badge priority-${reminder.priority}">${reminder.priority}</span>
          <span class="due-date">Due: ${formatDate(reminder.due)} ${reminder.due_time || ""}</span>
        </div>
        <div class="history-time">Completed on ${new Date(reminder.created_at).toLocaleString()}</div>
      `;
      historyList.appendChild(historyDiv);
    });
    
    // Add other history entries
    history.forEach(entry => {
      if (entry.action !== "completed") { // Skip completed entries as we show them above
        const historyDiv = document.createElement("div");
        historyDiv.className = "history-item";
        historyDiv.innerHTML = `
          <div class="history-action">${entry.action}</div>
          <div class="history-task">${entry.reminder.task}</div>
          <div class="history-time">${new Date(entry.timestamp).toLocaleString()}</div>
        `;
        historyList.appendChild(historyDiv);
      }
    });
  } catch (error) {
    console.error("Error loading history:", error);
  }
}

// ================== Notifications ==================
async function requestNotificationPermission() {
  if ("Notification" in window) {
    let perm = await Notification.requestPermission();
    console.log("Notification permission:", perm);
    if (perm === "granted") {
      showNotification("Notifications enabled!", "success");
    }
  }
}

document.getElementById("notificationToggle").addEventListener("change", e => {
  if (e.target.checked) {
    requestNotificationPermission();
  }
});

// Show notification message
function showNotification(message, type = "info") {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  
  // Style the notification
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 1000;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
    max-width: 300px;
  `;
  
  // Set background color based on type
  switch (type) {
    case "success":
      notification.style.backgroundColor = "#4CAF50";
      break;
    case "error":
      notification.style.backgroundColor = "#f44336";
      break;
    default:
      notification.style.backgroundColor = "#2196F3";
  }
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.style.opacity = "1";
    notification.style.transform = "translateX(0)";
  }, 100);
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = "0";
    notification.style.transform = "translateX(100%)";
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

// Check due reminders every minute
setInterval(async () => {
  try {
    const res = await fetch("/reminders");
    const reminders = await res.json();
    const now = new Date();

    reminders.forEach(r => {
      if (r.completed) return;
      if (!r.due) return;

      const dueDateTime = new Date(`${r.due}T${r.due_time || "00:00"}`);
      const diff = dueDateTime - now;

      // If within 1 minute of due time
      if (diff > 0 && diff < 60000) {
        if (Notification.permission === "granted") {
          new Notification("Reminder Due!", {
            body: `${r.task} (${r.category}) at ${r.due_time || "All day"}`,
            icon: "/static/bell.png"
          });
        }
        showNotification(`Reminder due: ${r.task}`, "info");
      }
    });
  } catch (error) {
    console.error("Error checking reminders:", error);
  }
}, 60000);

const ctx = document.getElementById("trendChart").getContext("2d");
new Chart(ctx, {
  type: "line",
  data: {
    labels: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
    datasets: [{
      label: "Reminders",
      data: [2, 4, 3, 5, 1, 0, 2],
      borderColor: "#007bff",
      fill: false
    }]
  }
});
