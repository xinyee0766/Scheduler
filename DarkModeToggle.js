document.addEventListener("DOMContentLoaded", () => {
  // Dark mode toggle
  const darkBtn = document.getElementById("darkModeToggle");
  
  darkBtn.addEventListener("click", () => {
    const html = document.documentElement;
    html.setAttribute(
      "data-theme",
      html.getAttribute("data-theme") === "dark" ? "light" : "dark"
    );
  });
});
