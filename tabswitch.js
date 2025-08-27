// Tab switching
  const tabs = document.querySelectorAll(".tab-btn");
  const sections = document.querySelectorAll(".section");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      // Remove active from all tabs & sections
      tabs.forEach(b => b.classList.remove("active"));
      sections.forEach(s => s.classList.remove("active"));

      // Activate clicked tab & its section
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.target);
      if(target) target.classList.add("active");
    });
  });

