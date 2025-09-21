<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Reminder Dashboard</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- Control-->
  <div class="controls">
    <h4>Color Theme</h4>
    <div class="color-picker">
      <div class="color-option" data-theme="default" style="background: #e0f7fa;"></div>
      <div class="color-option" data-theme="dark" style="background: #2c3e50;"></div>
      <div class="color-option" data-theme="green" style="background: #e8f5e8;"></div>
      <div class="color-option" data-theme="purple" style="background: #f3e5f5;"></div>
    </div>
    <div class="notification-toggle">
      <input type="checkbox" id="notificationToggle">
      <label for="notificationToggle">open notification</label>
    </div>
    <button onclick="testNotification()" style="width: 100%; margin-top: 10px; background: #28a745;">test button</button>
  </div>

  <form id="reminderForm">
    <h2>Add Reminder</h2>
    <label for="task">Reminder Name</label>
    <input type="text" id="task" placeholder="Exm:assignment" required>

    <label for="subject">Subject</label>
    <input type="text" id="subject" placeholder="Exm:Math" required>

    <label for="due">Deadline</label>
    <input type="date" id="due" required>

    <label for="due_time">Time</label>
    <input type="time" id="due_time" value="00:00">

    <button type="submit">Add Reminder</button>
  </form>

  <div id="dashboard">
    <h2>My Reminder Dashboard</h2>
    
    <!-- Tabs -->
    <div class="tabs">
      <button class="tab active" data-tab="current">REMINDER</button>
      <button class="tab" data-tab="history">HISTORY</button>
      <button class="tab" data-tab="notes">NOTES</button>
      <button class="tab" data-tab="todos">TO DO LIST</button>
    </div>
    
    <!-- Current Reminders Tab -->
    <div id="current" class="tab-content active">
      <table>
        <thead>
          <tr>
            <th>Reminder Name</th>
            <th>Subject</th>
            <th>Deadline</th>
            <th>Time</th>
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
    
    <!-- Notes Tab -->
    <div id="notes" class="tab-content">
      <div class="add-section">
        <h3>Add Note</h3>
        <div class="input-group">
          <textarea id="noteContent" placeholder="Enter your note here..." rows="3"></textarea>
          <button onclick="addNote()">Add Note</button>
        </div>
      </div>
      <div id="notesList"></div>
    </div>
    
    <!-- Todos Tab -->
    <div id="todos" class="tab-content">
      <div class="add-section">
        <h3>Add Todo</h3>
        <div class="input-group">
          <input type="text" id="todoTask" placeholder="Enter todo task...">
          <button onclick="addTodo()">Add Todo</button>
        </div>
      </div>
      <div id="todosList"></div>
    </div>
  </div>

<script>
var reminderList = document.getElementById("reminderList");
var historyList = document.getElementById("historyList");
var notesList = document.getElementById("notesList");
var todosList = document.getElementById("todosList");
var API_URL = "http://localhost:5000";

// Simple theme management
var themes = {
  default: '#e0f7fa',
  dark: '#2c3e50',
  green: '#e8f5e8',
  purple: '#f3e5f5'
};

// Apply theme
function applyTheme(themeName) {
  document.body.style.backgroundColor = themes[themeName];
  localStorage.setItem('selectedTheme', themeName);//remember what color user select
}

// Load saved theme
var savedTheme = localStorage.getItem('selectedTheme') || 'default';
applyTheme(savedTheme);

// Theme controls
var colorOptions = document.querySelectorAll('.color-option');
for (var i = 0; i < colorOptions.length; i++) {
  colorOptions[i].addEventListener('click', function() {
    var theme = this.dataset.theme;
    applyTheme(theme);
  });
}

// Notification permission and management
var notificationEnabled = localStorage.getItem('notificationEnabled') === 'true';
document.getElementById('notificationToggle').checked = notificationEnabled;

document.getElementById('notificationToggle').addEventListener('change', function(e) {
  notificationEnabled = e.target.checked;
  localStorage.setItem('notificationEnabled', notificationEnabled);
  
  if (notificationEnabled) {
    // 请求通知权限
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(function(permission) {
        if (permission === 'granted') {
          alert('Notification permissions have been granted! You will now receive notifications.');
        } else {
          alert('Notification permissions have been denied. You will still see pop-up alerts, but no system notifications will be displayed.');
        }
      });
    } else if (Notification.permission === 'denied') {
      alert('Notification permissions have been denied. You will still see pop-up alerts, but no system notifications will be displayed.');
    }
  }
});

// Tab management
var tabs = document.querySelectorAll('.tab');
for (var i = 0; i < tabs.length; i++) {
  tabs[i].addEventListener('click', function() {
    // Remove active class from all tabs and contents
    var allTabs = document.querySelectorAll('.tab');
    for (var j = 0; j < allTabs.length; j++) {
      allTabs[j].classList.remove('active');
    }
    var allContents = document.querySelectorAll('.tab-content');
    for (var k = 0; k < allContents.length; k++) {
      allContents[k].classList.remove('active');
    }
    
    // Add active class to clicked tab and corresponding content
    this.classList.add('active');
    var tabId = this.dataset.tab;
    document.getElementById(tabId).classList.add('active');
    
    // Load content based on tab
    if (tabId === 'history') {
      showHistory();
    } else if (tabId === 'notes') {
      showNotes();
    } else if (tabId === 'todos') {
      showTodos();
    }
  });
}

// Show reminder list with status
function showReminders() {
  reminderList.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">正在加载提醒...</td></tr>';
  
  fetch(API_URL + '/reminders')
    .then(function(response) {
      return response.json();
    })
    .then(function(reminders) {
      reminderList.innerHTML = "";
      
      if (reminders.length === 0) {
        reminderList.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">暂无提醒</td></tr>';
        return;
      }
      
      for (var i = 0; i < reminders.length; i++) {
        var r = reminders[i];
        if (r.completed) continue; // Skip completed reminders
        
        var dueTime = r.due_time || "00:00";
        var dueDateTime = new Date(r.due + 'T' + dueTime);
        var now = new Date();
        var timeDiff = dueDateTime - now;
        var hoursLeft = timeDiff / (1000 * 60 * 60);
        
        var statusClass = '';
        var statusText = '';
        
        if (timeDiff < 0) {
          statusClass = 'urgent';
          statusText = '已过期';
        } else if (hoursLeft <= 1) {
          statusClass = 'urgent';
          statusText = '1小时内到期';
        } else if (hoursLeft <= 24) {
          statusClass = 'due-soon';
          statusText = Math.ceil(hoursLeft) + '小时后到期';
        } else {
          var daysLeft = Math.ceil(hoursLeft / 24);
          statusText = daysLeft + '天后到期';
        }
        
        reminderList.innerHTML += 
          '<tr class="' + statusClass + '">' +
            '<td>' + r.task + '</td>' +
            '<td>' + r.subject + '</td>' +
            '<td>' + r.due + '</td>' +
            '<td>' + dueTime + '</td>' +
            '<td>' + statusText + '</td>' +
            '<td>' +
              '<button class="complete-btn" onclick="completeReminder(' + i + ')">完成</button>' +
              '<button class="delete-btn" onclick="deleteReminder(' + i + ')">删除</button>' +
            '</td>' +
          '</tr>';
      }
      
      // Check for notifications
      if (notificationEnabled) {
        checkNotifications();
      }
    })
    .catch(function(err) {
      console.error("Cannot get the reminder list：", err);
      // 显示友好的错误信息
      reminderList.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">暂无提醒</td></tr>';
    });
}

// Show notes
function showNotes() {
  // 先显示加载中状态
  notesList.innerHTML = '<p style="text-align: center; color: #666;">正在加载备忘录...</p>';
  
  fetch(API_URL + '/notes')
    .then(function(response) {
      return response.json();
    })
    .then(function(notes) {
      notesList.innerHTML = "";
      
      if (notes.length === 0) {
        notesList.innerHTML = '<p style="text-align: center; color: #666;">暂无备忘录</p>';
        return;
      }
      
      for (var i = notes.length - 1; i >= 0; i--) {
        var note = notes[i];
        var time = new Date(note.created_at).toLocaleString('zh-CN');
        notesList.innerHTML += 
          '<div class="note-item">' +
            '<div class="item-content">' +
              '<div>' + note.content + '</div>' +
              '<div class="history-time">' + time + '</div>' +
            '</div>' +
            '<div class="item-actions">' +
              '<button class="delete-btn" onclick="deleteNote(' + i + ')">删除</button>' +
            '</div>' +
          '</div>';
      }
    })
    .catch(function(err) {
      console.error("Cannot get notes：", err);
      // 显示友好的错误信息
      notesList.innerHTML = '<p style="text-align: center; color: #666;">暂无备忘录</p>';
    });
}

// Show history
function showHistory() {
  // 先显示加载中状态
  historyList.innerHTML = '<p style="text-align: center; color: #666;">正在加载历史记录...</p>';
  
  fetch(API_URL + '/history')
    .then(function(response) {
      return response.json();
    })
    .then(function(history) {
      historyList.innerHTML = "";
      
      if (history.length === 0) {
        historyList.innerHTML = '<p style="text-align: center; color: #666;">暂无历史记录</p>';
        return;
      }
      
      for (var i = history.length - 1; i >= 0; i--) {
        var entry = history[i];
        var time = new Date(entry.timestamp).toLocaleString('zh-CN');
        var actionText = entry.action === 'created' ? '创建' : 
                        entry.action === 'completed' ? '完成' : 
                        entry.action === 'deleted' ? '删除' : entry.action;
        
        var deletedClass = entry.action === 'deleted' ? 'deleted' : '';
        historyList.innerHTML += 
          '<div class="history-item ' + deletedClass + '">' +
            '<div class="item-content">' +
              '<div><strong>' + actionText + '</strong> - ' + entry.reminder.task + '</div>' +
              '<div style="font-size: 14px; color: #666;">科目: ' + entry.reminder.subject + ' | 截止: ' + entry.reminder.due + ' ' + (entry.reminder.due_time || '00:00') + '</div>' +
              '<div class="history-time">' + time + '</div>' +
            '</div>' +
          '</div>';
      }
    })
    .catch(function(err) {
      console.error("Cannot get history：", err);
      // 显示友好的错误信息，而不是"加载失败"
      historyList.innerHTML = '<p style="text-align: center; color: #666;">暂无历史记录</p>';
    });
}

// Show todos
function showTodos() {
  // 先显示加载中状态
  todosList.innerHTML = '<p style="text-align: center; color: #666;">正在加载待办事项...</p>';
  
  fetch(API_URL + '/todos')
    .then(function(response) {
      return response.json();
    })
    .then(function(todos) {
      todosList.innerHTML = "";
      
      if (todos.length === 0) {
        todosList.innerHTML = '<p style="text-align: center; color: #666;">暂无待办事项</p>';
        return;
      }
      
      for (var i = 0; i < todos.length; i++) {
        var todo = todos[i];
        var time = new Date(todo.created_at).toLocaleString('zh-CN');
        var completedClass = todo.completed ? 'completed' : '';
        var checkedAttr = todo.completed ? 'checked' : '';
        
        todosList.innerHTML += 
          '<div class="todo-item ' + completedClass + '">' +
            '<input type="checkbox" ' + checkedAttr + ' onchange="toggleTodo(' + i + ')">' +
            '<div class="item-content">' +
              '<div>' + todo.task + '</div>' +
              '<div class="history-time">' + time + '</div>' +
            '</div>' +
            '<div class="item-actions">' +
              '<button class="delete-btn" onclick="deleteTodo(' + i + ')">删除</button>' +
            '</div>' +
          '</div>';
      }
    })
    .catch(function(err) {
      console.error("Cannot get todos：", err);
      // 显示友好的错误信息
      todosList.innerHTML = '<p style="text-align: center; color: #666;">暂无待办事项</p>';
    });
}

// Popup alert function
function showPopupAlert(title, message, callback) {
  var overlay = document.createElement('div');
  overlay.className = 'popup-overlay';
  
  var popup = document.createElement('div');
  popup.className = 'popup-alert';
  popup.innerHTML = 
    '<h3>' + title + '</h3>' +
    '<p>' + message + '</p>' +
    '<button onclick="closePopup()">确定</button>' +
    '<button class="secondary" onclick="closePopup()">取消</button>';
  
  overlay.appendChild(popup);
  document.body.appendChild(overlay);
  
  window.closePopup = function() {
    document.body.removeChild(overlay);
    if (callback) callback();
  };
}

// Check notifications with popup alerts
function checkNotifications() {
  if (!notificationEnabled) {
    return;
  }
  
  fetch(API_URL + '/upcoming')
    .then(function(response) {
      return response.json();
    })
    .then(function(upcoming) {
      for (var i = 0; i < upcoming.length; i++) {
        var reminder = upcoming[i];
        if (reminder.urgent) {
          // 播放系统提示音
          playNotificationSound();
          
          // Show popup alert for urgent reminders
          showPopupAlert(
            '紧急提醒: ' + reminder.task,
            '科目: ' + reminder.subject + ' - 1小时内到期！',
            function() {
              console.log('User acknowledged urgent reminder');
            }
          );
          
          // Also show browser notification if permission granted
          if (Notification.permission === 'granted') {
            new Notification('紧急提醒: ' + reminder.task, {
              body: '科目: ' + reminder.subject + ' - 1小时内到期！',
              icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="red"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
              tag: 'urgent-' + reminder.id
            });
          }
        } else if (reminder.hours_left <= 24) {
          // 播放系统提示音
          playNotificationSound();
          
          // Show popup alert for upcoming reminders
          showPopupAlert(
            '提醒通知: ' + reminder.task,
            '科目: ' + reminder.subject + ' - ' + Math.ceil(reminder.hours_left) + '小时后到期',
            function() {
              console.log('User acknowledged upcoming reminder');
            }
          );
          
          // Also show browser notification if permission granted
          if (Notification.permission === 'granted') {
            new Notification('提醒: ' + reminder.task, {
              body: '科目: ' + reminder.subject + ' - ' + Math.ceil(reminder.hours_left) + '小时后到期',
              icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="orange"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
              tag: 'upcoming-' + reminder.id
            });
          }
        }
      }
    })
    .catch(function(err) {
      console.error("Notification check failed：", err);
    });
}

// 测试通知功能
function testNotification() {
  // 播放提示音
  playNotificationSound();
  
  // 显示弹窗
  showPopupAlert(
    '测试通知',
    '这是一个测试通知！如果您看到这个弹窗并听到提示音，说明通知功能正常工作。',
    function() {
      console.log('测试通知被确认');
    }
  );
  
  // 显示系统通知（如果权限允许）
  if (Notification.permission === 'granted') {
    new Notification('测试通知', {
      body: '通知功能正常工作！',
      icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="green"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
      tag: 'test-notification'
    });
  } else if (Notification.permission === 'default') {
    alert('请先启用通知权限，然后再次点击测试按钮');
  } else {
    alert('系统通知权限被拒绝，但弹窗和提示音仍然有效');
  }
}

// 播放系统提示音
function playNotificationSound() {
  try {
    // 创建音频上下文
    var audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // 创建振荡器
    var oscillator = audioContext.createOscillator();
    var gainNode = audioContext.createGain();
    
    // 连接节点
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // 设置频率和音量
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800Hz
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    
    // 播放声音
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2); // 播放0.2秒
    
    // 播放第二个音调
    setTimeout(function() {
      var oscillator2 = audioContext.createOscillator();
      var gainNode2 = audioContext.createGain();
      
      oscillator2.connect(gainNode2);
      gainNode2.connect(audioContext.destination);
      
      oscillator2.frequency.setValueAtTime(1000, audioContext.currentTime); // 1000Hz
      gainNode2.gain.setValueAtTime(0.3, audioContext.currentTime);
      
      oscillator2.start(audioContext.currentTime);
      oscillator2.stop(audioContext.currentTime + 0.2);
    }, 300);
    
  } catch (err) {
    console.log("无法播放提示音:", err);
    // 备用方案：使用简单的beep声音
    try {
      var audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU6k9n1unEiBC13yO/eizEIHWq+8+OWT');
      audio.play();
    } catch (e) {
      console.log("备用提示音也无法播放");
    }
  }
}

// Add note function
function addNote() {
  var content = document.getElementById('noteContent').value.trim();
  if (!content) {
    alert('请输入备忘录内容');
    return;
  }
  
  fetch(API_URL + '/notes', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: content })
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Note added:", result);
    document.getElementById('noteContent').value = '';
    showNotes();
  })
  .catch(function(err) {
    console.error("Add note failed:", err);
    alert("添加备忘录失败");
  });
}

// Delete note function
function deleteNote(index) {
  fetch(API_URL + '/notes/' + index, {
    method: "DELETE"
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Note deleted:", result);
    showNotes();
  })
  .catch(function(err) {
    console.error("Delete note failed:", err);
    alert("删除备忘录失败");
  });
}

// Add todo function
function addTodo() {
  var task = document.getElementById('todoTask').value.trim();
  if (!task) {
    alert('请输入待办事项');
    return;
  }
  
  fetch(API_URL + '/todos', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task: task })
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Todo added:", result);
    document.getElementById('todoTask').value = '';
    showTodos();
  })
  .catch(function(err) {
    console.error("Add todo failed:", err);
    alert("添加待办事项失败");
  });
}

// Toggle todo function
function toggleTodo(index) {
  fetch(API_URL + '/todos/' + index + '/toggle', {
    method: "PUT"
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Todo toggled:", result);
    showTodos();
  })
  .catch(function(err) {
    console.error("Toggle todo failed:", err);
    alert("更新待办事项失败");
  });
}

// Delete todo function
function deleteTodo(index) {
  fetch(API_URL + '/todos/' + index, {
    method: "DELETE"
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Todo deleted:", result);
    showTodos();
  })
  .catch(function(err) {
    console.error("Delete todo failed:", err);
    alert("删除待办事项失败");
  });
}

// Complete reminder function
function completeReminder(index) {
  fetch(API_URL + '/reminders/' + index + '/complete', {
    method: "PUT"
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Reminder completed:", result);
    showReminders();
  })
  .catch(function(err) {
    console.error("Complete reminder failed:", err);
    alert("完成提醒失败");
  });
}

// add reminder
document.getElementById("reminderForm").addEventListener("submit", function(e) {
  e.preventDefault();
  var task = document.getElementById("task").value.trim();
  var subject = document.getElementById("subject").value.trim();
  var due = document.getElementById("due").value;
  var due_time = document.getElementById("due_time").value;

  if (!task || !subject || !due) {
    alert("please write the task");
    return;
  }

  fetch(API_URL + '/reminders', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task: task, subject: subject, due: due, due_time: due_time })
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("Successful：", result);
    showReminders();
    document.getElementById("reminderForm").reset();
  })
  .catch(function(err) {
    console.error("Fail：", err);
    alert("添加提醒失败，请检查服务器是否运行");
  });
});

// delete reminder
function deleteReminder(index) {
  fetch(API_URL + '/reminders/' + index, {
    method: "DELETE"
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(result) {
    console.log("delete successfully：", result);
    showReminders();
  })
  .catch(function(err) {
    console.error("delete failed：", err);
    alert("删除提醒失败");
  });
}

// Initialize
showReminders();

// Check notifications every 1 minute
setInterval(() => {
  if (notificationEnabled) {
    checkNotifications();
  }
}, 60 * 1000);
</script>
</body>
</html>
