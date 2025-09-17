// DarkModeToggle.js
(function () {
  // Helper to set the button label
  function updateButtonLabel(btn, theme) {
    if (!btn) return;
    btn.textContent = theme === "dark" ? "☀️ Light Mode" : "🌗 Dark Mode";
  }

  function init() {
    const html = document.documentElement;
    const btn = document.getElementById("darkModeToggle");

    if (!btn) {
      console.error("DarkModeToggle: button with id 'darkModeToggle' not found.");
      return;
    }

    // Initialize theme from localStorage (default to light)
    const saved = localStorage.getItem("site-theme") || html.getAttribute("data-theme") || "light";
    html.setAttribute("data-theme", saved);
    updateButtonLabel(btn, saved);

    // Click handler toggles theme, saves and updates label
    btn.addEventListener("click", () => {
      const current = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", current);
      localStorage.setItem("site-theme", current);
      updateButtonLabel(btn, current);
      console.log("DarkModeToggle: theme ->", current);
    });

    console.log("DarkModeToggle: initialized (theme =", saved + ")");
  }

  // Prefer DOMContentLoaded but also handle if DOM already loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
