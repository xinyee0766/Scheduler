const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const browseTrigger = document.getElementById("browseTrigger");
const fileList = document.getElementById("fileList");

function handleFiles(files) {
  Array.from(files).forEach(file => {
    const li = document.createElement("li");

    // Create blob URL so we can open/download the file
    const fileURL = URL.createObjectURL(file);

    // Preview container
    const preview = document.createElement("div");
    preview.classList.add("file-preview");

    if (file.type.startsWith("image/")) {
      // Image preview
      const img = document.createElement("img");
      img.src = fileURL;
      img.alt = file.name;
      preview.appendChild(img);
    } else if (file.type === "application/pdf") {
      // PDF icon
      const icon = document.createElement("div");
      icon.textContent = "📄";
      icon.classList.add("file-icon");
      preview.appendChild(icon);
    } else {
      // Generic file icon
      const icon = document.createElement("div");
      icon.textContent = "📁";
      icon.classList.add("file-icon");
      preview.appendChild(icon);
    }

    // Clickable link
    const link = document.createElement("a");
    link.href = fileURL;
    link.target = "_blank";
    link.download = file.name;
    link.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    li.appendChild(preview);
    li.appendChild(link);
    fileList.appendChild(li);
  });
}

// Prevent default browser behavior
["dragenter", "dragover", "dragleave", "drop"].forEach(evt => {
  dropzone.addEventListener(evt, e => {
    e.preventDefault();
    e.stopPropagation();
  });
});

// Highlight on dragover
["dragenter", "dragover"].forEach(evt => {
  dropzone.addEventListener(evt, () => dropzone.classList.add("dragover"));
});
["dragleave", "drop"].forEach(evt => {
  dropzone.addEventListener(evt, () => dropzone.classList.remove("dragover"));
});

// Handle dropped files
dropzone.addEventListener("drop", e => handleFiles(e.dataTransfer.files));

// Handle browse button
browseTrigger.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => handleFiles(e.target.files));
