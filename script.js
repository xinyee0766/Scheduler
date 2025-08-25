// Dark mode toggle
const darkBtn = document.getElementById("darkModeToggle");
darkBtn.addEventListener("click", () => {
  const html = document.documentElement;
  html.setAttribute(
    "data-theme",
    html.getAttribute("data-theme") === "dark" ? "light" : "dark"
  );
});

// Tab switching
const tabs = document.querySelectorAll(".tab-btn");
const sections = document.querySelectorAll(".section");

tabs.forEach(btn => {
  btn.addEventListener("click", () => {
    tabs.forEach(b => b.classList.remove("active"));
    sections.forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.target).classList.add("active");
  });
});
