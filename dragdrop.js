document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseTrigger = document.getElementById("browseTrigger");
  const preview = document.getElementById("preview");

  // File management buttons from HTML
  const editToggle = document.getElementById("editToggle");
  const deleteSelectedBtn = document.getElementById("deleteSelected");
  const deleteAllBtn = document.getElementById("deleteAll");

  let uploadedFiles = [];
  let editMode = false;

  // ========== File Handling ==========
  function handleFiles(files) {
    if (!files.length) return;
    uploadedFiles.push(...files);
    renderPreviews();
  }

  function renderPreviews() {
    preview.innerHTML = "";

    uploadedFiles.forEach((file, index) => {
      const fileURL = URL.createObjectURL(file);

      // Container
      const item = document.createElement("div");
      item.classList.add("preview-item");

      // Edit checkbox
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.classList.add("file-checkbox");
      checkbox.dataset.index = index;
      checkbox.style.display = editMode ? "block" : "none";
      item.appendChild(checkbox);

      // Preview element
      let previewElement;
      if (file.type.startsWith("image/")) {
        previewElement = document.createElement("img");
        previewElement.src = fileURL;
        previewElement.alt = file.name;
      } else if (file.type === "application/pdf" && typeof pdfjsLib !== "undefined") {
        previewElement = document.createElement("canvas");
        const fileReader = new FileReader();
        fileReader.onload = function () {
          const typedarray = new Uint8Array(this.result);
          pdfjsLib.getDocument(typedarray).promise.then(pdf => {
            pdf.getPage(1).then(page => {
              const viewport = page.getViewport({ scale: 0.5 });
              const context = previewElement.getContext("2d");
              previewElement.height = viewport.height;
              previewElement.width = viewport.width;
              page.render({ canvasContext: context, viewport });
            });
          });
        };
        fileReader.readAsArrayBuffer(file);
      } else {
        previewElement = document.createElement("div");
        previewElement.textContent = "📁";
        previewElement.classList.add("file-icon");
      }

      // Wrap preview in link
      const previewLink = document.createElement("a");
      previewLink.href = fileURL;
      previewLink.target = "_blank";
      previewLink.download = file.name;
      previewLink.classList.add("preview-link");
      previewLink.appendChild(previewElement);
      item.appendChild(previewLink);

      // Filename
      const filename = document.createElement("div");
      filename.classList.add("file-name");
      filename.textContent = file.name;
      item.appendChild(filename);

      preview.appendChild(item);
    });
  }

  // ========== Drag & Drop ==========
  ["dragenter", "dragover", "dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, () => dropzone.classList.add("dragover"));
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, () => dropzone.classList.remove("dragover"));
  });

  dropzone.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    handleFiles([...files]);
  });

  browseTrigger.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", e => {
    handleFiles([...e.target.files]);
    fileInput.value = ""; // reset so same file can be uploaded again
  });

  // ========== File Actions ==========
  editToggle.addEventListener("click", () => {
    editMode = !editMode;
    document.querySelectorAll(".file-checkbox").forEach(cb => {
      cb.style.display = editMode ? "block" : "none";
    });

    deleteSelectedBtn.style.display = editMode ? "inline-block" : "none";
    deleteAllBtn.style.display = editMode ? "inline-block" : "none";
    editToggle.textContent = editMode ? "✅ Done" : "✏️ Edit";
  });

  deleteSelectedBtn.addEventListener("click", () => {
    const selected = Array.from(document.querySelectorAll(".file-checkbox:checked"))
      .map(cb => parseInt(cb.dataset.index));

    uploadedFiles = uploadedFiles.filter((_, i) => !selected.includes(i));
    renderPreviews();
  });

  deleteAllBtn.addEventListener("click", () => {
    uploadedFiles = [];
    renderPreviews();
  });
});
