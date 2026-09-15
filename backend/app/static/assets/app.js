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
  const layoutMode = document.getElementById("layoutMode");
  const layoutField = document.getElementById("layoutField");
  const layoutHint = document.getElementById("layoutHint");
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

  function syncLayoutVisibility() {
    const isPdfToDocx =
      selectedFile &&
      extOf(selectedFile.name) === "pdf" &&
      (targetFormat.value === "docx" || targetFormat.value === "doc");
    layoutField.classList.toggle("hidden", !isPdfToDocx);
    if (!isPdfToDocx) {
      layoutHint.classList.add("hidden");
    }
  }

  async function analyzeSelectedPdf(file) {
    if (extOf(file.name) !== "pdf") {
      layoutHint.classList.add("hidden");
      return;
    }
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/analyze", { method: "POST", body });
      if (!res.ok) return;
      const data = await res.json();
      const modeLabel =
        data.recommended_mode === "visual" ? "視覺保版" : "可編輯文字";
      layoutHint.textContent = `偵測：${data.reason} → 建議「${modeLabel}」`;
      layoutHint.classList.remove("hidden");
      if (layoutMode.value === "auto") {
        // keep auto; hint explains what auto will do
      }
    } catch (_) {
      /* optional hint */
    }
  }

  function setFile(file) {
    selectedFile = file;
    clearError();
    resultEl.classList.add("hidden");
    statusEl.classList.add("hidden");
    layoutHint.classList.add("hidden");
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
      syncLayoutVisibility();
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

    if (ext === "pdf" && options.includes("docx")) {
      targetFormat.value = "docx";
    }
    convertBtn.disabled = false;
    syncLayoutVisibility();
    analyzeSelectedPdf(file);
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

  targetFormat.addEventListener("change", syncLayoutVisibility);

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

  const messagesVisual = [
    "正在分析版面複雜度…",
    "逐頁高清渲染中…",
    "寫入 Word 頁面尺寸…",
    "輸出保版檔案…",
  ];
  const messagesEditable = [
    "正在解析文字區塊…",
    "重建段落與表格…",
    "對齊圖片位置…",
    "輸出可編輯 Word…",
  ];

  convertBtn.addEventListener("click", async () => {
    if (!selectedFile || !targetFormat.value) return;
    clearError();
    resultEl.classList.add("hidden");
    statusEl.classList.remove("hidden");
    convertBtn.disabled = true;

    const useVisualMsgs =
      layoutMode.value === "visual" ||
      layoutMode.value === "auto" ||
      targetFormat.value !== "docx";
    const messages = useVisualMsgs ? messagesVisual : messagesEditable;

    let i = 0;
    statusText.textContent = messages[0];
    const ticker = setInterval(() => {
      i = (i + 1) % messages.length;
      statusText.textContent = messages[i];
    }, 1400);

    const body = new FormData();
    body.append("file", selectedFile);
    body.append("target_format", targetFormat.value);
    body.append("layout_mode", layoutMode.value || "auto");

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
      const resultNote = resultEl.querySelector("p");
      if (resultNote) {
        resultNote.textContent =
          layoutMode.value === "editable"
            ? "已輸出可編輯文字（複雜設計稿可能仍有位移）。"
            : "已用視覺保版輸出，版面與原 PDF 對齊。";
      }
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
        ? "LibreOffice 已就緒。PDF→Word 對設計稿預設視覺保版。"
        : "PDF→Word 已改為視覺保版（Canva／履歷不跑版）。安裝 LibreOffice 可擴充更多 Office 路徑。";

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

  syncLayoutVisibility();
  loadFormats();
})();
