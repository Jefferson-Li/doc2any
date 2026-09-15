(() => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropIdle = document.getElementById("dropIdle");
  const fileChip = document.getElementById("fileChip");
  const fileExt = document.getElementById("fileExt");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const clearFile = document.getElementById("clearFile");
  const targetFormat = document.getElementById("targetFormat");
  const convertBtn = document.getElementById("convertBtn");
  const statusEl = document.getElementById("status");
  const statusText = document.getElementById("statusText");
  const resultEl = document.getElementById("result");
  const resultName = document.getElementById("resultName");
  const downloadBtn = document.getElementById("downloadBtn");
  const errorEl = document.getElementById("error");
  const formatGrid = document.getElementById("formatGrid");
  const engineNote = document.getElementById("engineNote");

  let selectedFile = null;
  let routes = {};
  let downloadUrl = null;

  const DEFAULT_TARGETS = ["docx", "pdf", "png", "jpg", "html", "txt"];

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function extOf(name) {
    const parts = name.split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove("hidden");
  }

  function clearError() {
    errorEl.textContent = "";
    errorEl.classList.add("hidden");
  }

  function setFile(file) {
    selectedFile = file;
    clearError();
    resultEl.classList.add("hidden");
    statusEl.classList.add("hidden");
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      downloadUrl = null;
    }

    if (!file) {
      dropIdle.classList.remove("hidden");
      fileChip.classList.add("hidden");
      targetFormat.innerHTML = '<option value="">先上傳檔案</option>';
      targetFormat.disabled = true;
      convertBtn.disabled = true;
      return;
    }

    const ext = extOf(file.name) || "FILE";
    fileExt.textContent = ext.toUpperCase();
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    dropIdle.classList.add("hidden");
    fileChip.classList.remove("hidden");

    const options = routes[ext] || DEFAULT_TARGETS;
    targetFormat.innerHTML = options
      .map((t) => `<option value="${t}">.${t.toUpperCase()}</option>`)
      .join("");
    targetFormat.disabled = false;

    // Prefer docx when source is pdf
    if (ext === "pdf" && options.includes("docx")) {
      targetFormat.value = "docx";
    }
    convertBtn.disabled = false;
  }

  function openPicker() {
    fileInput.click();
  }

  dropzone.addEventListener("click", (e) => {
    if (e.target === clearFile) return;
    openPicker();
  });

  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (file) setFile(file);
  });

  clearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.value = "";
    setFile(null);
  });

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) setFile(file);
  });

  const messages = [
    "正在分析版面…",
    "重建段落與表格…",
    "保留圖片位置…",
    "輸出目標格式…",
  ];

  convertBtn.addEventListener("click", async () => {
    if (!selectedFile || !targetFormat.value) return;
    clearError();
    resultEl.classList.add("hidden");
    statusEl.classList.remove("hidden");
    convertBtn.disabled = true;

    let i = 0;
    statusText.textContent = messages[0];
    const ticker = setInterval(() => {
      i = (i + 1) % messages.length;
      statusText.textContent = messages[i];
    }, 1400);

    const body = new FormData();
    body.append("file", selectedFile);
    body.append("target_format", targetFormat.value);

    try {
      const res = await fetch("/api/convert", { method: "POST", body });
      if (!res.ok) {
        let detail = "轉換失敗";
        try {
          const data = await res.json();
          detail = data.detail || detail;
        } catch (_) {
          /* ignore */
        }
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }

      const blob = await res.blob();
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      const outName =
        match?.[1] ||
        `${selectedFile.name.replace(/\.[^.]+$/, "")}.${targetFormat.value}`;

      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
      downloadUrl = URL.createObjectURL(blob);
      downloadBtn.href = downloadUrl;
      downloadBtn.download = outName;
      resultName.textContent = outName;
      resultEl.classList.remove("hidden");
    } catch (err) {
      showError(err.message || "轉換失敗，請稍後再試");
    } finally {
      clearInterval(ticker);
      statusEl.classList.add("hidden");
      convertBtn.disabled = !selectedFile;
    }
  });

  async function loadFormats() {
    try {
      const res = await fetch("/api/formats");
      const data = await res.json();
      routes = data.routes || {};
      engineNote.textContent = data.libreoffice
        ? "LibreOffice 已就緒，Office 互轉可保真匯出。"
        : "核心引擎已就緒（PDF→DOCX 保版）。安裝 LibreOffice 後可擴充更多 Office 路徑。";

      formatGrid.innerHTML = Object.entries(routes)
        .map(
          ([from, to]) => `
          <div class="format-card">
            <strong>.${from}</strong>
            <span>→ ${to.map((t) => "." + t).join(" · ")}</span>
          </div>`
        )
        .join("");
    } catch (_) {
      engineNote.textContent = "無法讀取引擎狀態，仍可嘗試上傳轉換。";
    }
  }

  loadFormats();
})();
