(() => {
  const I18N = {
    "zh-Hant": {
      "meta.title": "Doc2Any — 不跑版文件轉換",
      "meta.description":
        "上傳任意格式，轉成你要的格式。PDF 轉 Word 盡量保留版面、表格與圖片。",
      "nav.how": "怎麼用",
      "nav.formats": "支援格式",
      "hero.title": "上傳任意格式，轉成你要的格式，盡量不跑版。",
      "hero.lede":
        "Canva／多欄履歷預設用「視覺保版」整頁對齊；簡單文件可改可編輯文字模式。",
      "dropzone.aria": "上傳檔案",
      "dropzone.title": "拖曳檔案到這裡",
      "dropzone.sub": "或點擊選擇 · 最大 50MB",
      "dropzone.clear": "清除檔案",
      "controls.target": "轉成",
      "controls.layout": "版面模式",
      "controls.convert": "開始轉換",
      "controls.uploadFirst": "先上傳檔案",
      "layout.auto": "自動（建議）",
      "layout.visual": "視覺保版（不跑版）",
      "layout.editable": "可編輯文字",
      "status.default": "正在分析版面…",
      "status.v1": "正在分析版面複雜度…",
      "status.v2": "逐頁高清渲染中…",
      "status.v3": "寫入 Word 頁面尺寸…",
      "status.v4": "輸出保版檔案…",
      "status.e1": "正在解析文字區塊…",
      "status.e2": "重建段落與表格…",
      "status.e3": "對齊圖片位置…",
      "status.e4": "輸出可編輯 Word…",
      "result.default": "轉換完成，版面已盡量保留。",
      "result.visual": "已用視覺保版輸出，版面與原 PDF 對齊。",
      "result.editable": "已輸出可編輯文字（複雜設計稿可能仍有位移）。",
      "result.download": "下載檔案",
      "error.convert": "轉換失敗",
      "error.retry": "轉換失敗，請稍後再試",
      "how.title": "怎麼做到比較不跑版",
      "how.lede": "針對不同來源，選用最適合的轉換引擎。",
      "how.s1.title": "不是 OCR 問題時",
      "how.s1.body":
        "有文字層的 Canva／多欄 PDF，用文字重建會把欄位打散；應改視覺保版。",
      "how.s2.title": "視覺保版（預設）",
      "how.s2.body": "逐頁高清渲染進 Word，版面與原 PDF 對齊，適合履歷與設計稿。",
      "how.s3.title": "可編輯文字",
      "how.s3.body": "單欄論文／報告較適合；掃描件需先 OCR 才有可選文字。",
      "formats.title": "支援路徑",
      "formats.loading": "正在讀取引擎狀態…",
      "formats.loReady": "LibreOffice 已就緒。PDF→Word 對設計稿預設視覺保版。",
      "formats.coreReady":
        "PDF→Word 已改為視覺保版（Canva／履歷不跑版）。安裝 LibreOffice 可擴充更多 Office 路徑。",
      "formats.unavailable": "無法讀取引擎狀態，仍可嘗試上傳轉換。",
      "env.banner": "目前環境：{label}",
      "hint.mode.visual": "視覺保版",
      "hint.mode.editable": "可編輯文字",
      "hint.scanned": "掃描影像 PDF（無文字層，需 OCR 才能可編輯）",
      "hint.complex": "設計稿／多欄絕對定位（如 Canva），文字重建會跑版",
      "hint.simple": "文字流動版面，可嘗試可編輯重建",
      "hint.template": "偵測：{reason} → 建議「{mode}」",
      footer: "Doc2Any · 本機轉換，檔案不會送到第三方雲端",
    },
    en: {
      "meta.title": "Doc2Any — Layout-safe document conversion",
      "meta.description":
        "Upload any format and convert to your target. PDF to Word with layout-aware modes.",
      "nav.how": "How it works",
      "nav.formats": "Formats",
      "hero.title": "Upload any format, convert to yours—without wrecking the layout.",
      "hero.lede":
        "Canva / multi-column resumes default to visual fidelity. Simple docs can use editable text mode.",
      "dropzone.aria": "Upload a file",
      "dropzone.title": "Drop a file here",
      "dropzone.sub": "or click to browse · max 50MB",
      "dropzone.clear": "Clear file",
      "controls.target": "Convert to",
      "controls.layout": "Layout mode",
      "controls.convert": "Convert",
      "controls.uploadFirst": "Upload a file first",
      "layout.auto": "Auto (recommended)",
      "layout.visual": "Visual (layout-safe)",
      "layout.editable": "Editable text",
      "status.default": "Analyzing layout…",
      "status.v1": "Checking layout complexity…",
      "status.v2": "Rendering pages in high quality…",
      "status.v3": "Writing Word page size…",
      "status.v4": "Exporting layout-safe file…",
      "status.e1": "Parsing text blocks…",
      "status.e2": "Rebuilding paragraphs & tables…",
      "status.e3": "Aligning images…",
      "status.e4": "Exporting editable Word…",
      "result.default": "Done. Layout preserved as much as possible.",
      "result.visual": "Exported with visual fidelity—aligned to the original PDF.",
      "result.editable":
        "Editable text exported (complex designs may still shift).",
      "result.download": "Download",
      "error.convert": "Conversion failed",
      "error.retry": "Conversion failed. Please try again.",
      "how.title": "How we avoid broken layouts",
      "how.lede": "Pick the engine that fits the source document.",
      "how.s1.title": "When it is not an OCR issue",
      "how.s1.body":
        "Text-layer Canva / multi-column PDFs break under text rebuild—use visual mode.",
      "how.s2.title": "Visual fidelity (default)",
      "how.s2.body":
        "Each page is rendered into Word at high quality—ideal for resumes and design PDFs.",
      "how.s3.title": "Editable text",
      "how.s3.body":
        "Best for single-column papers/reports. Scanned PDFs need OCR first.",
      "formats.title": "Supported routes",
      "formats.loading": "Loading engine status…",
      "formats.loReady":
        "LibreOffice is ready. PDF→Word uses visual fidelity for design PDFs by default.",
      "formats.coreReady":
        "PDF→Word uses visual fidelity (layout-safe for Canva/resumes). Install LibreOffice for more Office routes.",
      "formats.unavailable":
        "Could not load engine status. You can still try converting.",
      "env.banner": "Environment: {label}",
      "hint.mode.visual": "Visual",
      "hint.mode.editable": "Editable text",
      "hint.scanned": "Scanned image PDF (no text layer—OCR needed for editable text)",
      "hint.complex":
        "Designed / multi-column absolute layout (e.g. Canva)—text rebuild will break",
      "hint.simple": "Flowing text layout—editable rebuild may work",
      "hint.template": "Detected: {reason} → recommend “{mode}”",
      footer: "Doc2Any · Local conversion—files never leave your machine",
    },
  };

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
  const resultNote = document.getElementById("resultNote");
  const downloadBtn = document.getElementById("downloadBtn");
  const errorEl = document.getElementById("error");
  const formatGrid = document.getElementById("formatGrid");
  const engineNote = document.getElementById("engineNote");
  const envBanner = document.getElementById("envBanner");
  const langButtons = document.querySelectorAll(".lang-btn");

  let selectedFile = null;
  let routes = {};
  let downloadUrl = null;
  let formatsData = null;
  let healthData = null;
  let lastAnalyze = null;
  let lang =
    localStorage.getItem("doc2any_lang") ||
    (navigator.language && navigator.language.toLowerCase().startsWith("zh")
      ? "zh-Hant"
      : "en");

  if (!I18N[lang]) lang = "zh-Hant";

  const DEFAULT_TARGETS = ["docx", "pdf", "png", "jpg", "html", "txt"];

  function t(key) {
    return I18N[lang][key] || I18N["zh-Hant"][key] || key;
  }

  function applyStaticI18n() {
    document.documentElement.lang = lang;
    document.title = t("meta.title");
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", t("meta.description"));

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      if (el.tagName === "OPTION") {
        el.textContent = t(key);
      } else {
        el.textContent = t(key);
      }
    });

    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      if (key) el.setAttribute("aria-label", t(key));
    });

    langButtons.forEach((btn) => {
      const active = btn.dataset.lang === lang;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });

    // Refresh dynamic bits that depend on language
    if (!selectedFile) {
      targetFormat.innerHTML = `<option value="">${t("controls.uploadFirst")}</option>`;
    } else {
      refreshTargetOptions(false);
    }
    renderEngineNote();
    renderAnalyzeHint();
    renderEnvBanner();
  }

  function renderEnvBanner() {
    if (!envBanner) return;
    const label = healthData?.label;
    if (!label || healthData?.environment === "production") {
      envBanner.classList.add("hidden");
      envBanner.textContent = "";
      return;
    }
    envBanner.textContent = t("env.banner").replace("{label}", label);
    envBanner.classList.remove("hidden");
  }

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
    } else {
      renderAnalyzeHint();
    }
  }

  function analyzeReasonKey(data) {
    if (!data) return null;
    if (data.is_scanned) return "hint.scanned";
    if (data.complex_layout) return "hint.complex";
    return "hint.simple";
  }

  function renderAnalyzeHint() {
    if (!lastAnalyze || !selectedFile || extOf(selectedFile.name) !== "pdf") {
      return;
    }
    const modeKey =
      lastAnalyze.recommended_mode === "visual"
        ? "hint.mode.visual"
        : "hint.mode.editable";
    const reason = t(analyzeReasonKey(lastAnalyze));
    layoutHint.textContent = t("hint.template")
      .replace("{reason}", reason)
      .replace("{mode}", t(modeKey));
    layoutHint.classList.remove("hidden");
  }

  async function analyzeSelectedPdf(file) {
    if (extOf(file.name) !== "pdf") {
      lastAnalyze = null;
      layoutHint.classList.add("hidden");
      return;
    }
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/analyze", { method: "POST", body });
      if (!res.ok) return;
      lastAnalyze = await res.json();
      renderAnalyzeHint();
    } catch (_) {
      /* optional hint */
    }
  }

  function refreshTargetOptions(preferDocx) {
    if (!selectedFile) return;
    const ext = extOf(selectedFile.name);
    const options = routes[ext] || DEFAULT_TARGETS;
    const prev = targetFormat.value;
    targetFormat.innerHTML = options
      .map((x) => `<option value="${x}">.${x.toUpperCase()}</option>`)
      .join("");
    if (preferDocx && ext === "pdf" && options.includes("docx")) {
      targetFormat.value = "docx";
    } else if (options.includes(prev)) {
      targetFormat.value = prev;
    }
  }

  function setFile(file) {
    selectedFile = file;
    clearError();
    resultEl.classList.add("hidden");
    statusEl.classList.add("hidden");
    layoutHint.classList.add("hidden");
    lastAnalyze = null;
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      downloadUrl = null;
    }

    if (!file) {
      dropIdle.classList.remove("hidden");
      fileChip.classList.add("hidden");
      targetFormat.innerHTML = `<option value="">${t("controls.uploadFirst")}</option>`;
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

    targetFormat.disabled = false;
    refreshTargetOptions(true);
    convertBtn.disabled = false;
    syncLayoutVisibility();
    analyzeSelectedPdf(file);
  }

  function openPicker() {
    fileInput.click();
  }

  langButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.lang;
      if (!next || next === lang || !I18N[next]) return;
      lang = next;
      localStorage.setItem("doc2any_lang", lang);
      applyStaticI18n();
    });
  });

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
    const messages = useVisualMsgs
      ? [t("status.v1"), t("status.v2"), t("status.v3"), t("status.v4")]
      : [t("status.e1"), t("status.e2"), t("status.e3"), t("status.e4")];

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
        let detail = t("error.convert");
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
      if (resultNote) {
        resultNote.textContent =
          layoutMode.value === "editable" ? t("result.editable") : t("result.visual");
      }
      resultEl.classList.remove("hidden");
    } catch (err) {
      showError(err.message || t("error.retry"));
    } finally {
      clearInterval(ticker);
      statusEl.classList.add("hidden");
      convertBtn.disabled = !selectedFile;
    }
  });

  function renderEngineNote() {
    if (!formatsData) {
      engineNote.textContent = t("formats.loading");
      return;
    }
    engineNote.textContent = formatsData.libreoffice
      ? t("formats.loReady")
      : t("formats.coreReady");
  }

  async function loadFormats() {
    try {
      const [formatsRes, healthRes] = await Promise.all([
        fetch("/api/formats"),
        fetch("/api/health"),
      ]);
      formatsData = await formatsRes.json();
      if (healthRes.ok) {
        healthData = await healthRes.json();
      }
      routes = formatsData.routes || {};
      renderEngineNote();
      renderEnvBanner();

      formatGrid.innerHTML = Object.entries(routes)
        .map(
          ([from, to]) => `
          <div class="format-card">
            <strong>.${from}</strong>
            <span>→ ${to.map((x) => "." + x).join(" · ")}</span>
          </div>`
        )
        .join("");
    } catch (_) {
      formatsData = null;
      engineNote.textContent = t("formats.unavailable");
    }
  }

  applyStaticI18n();
  syncLayoutVisibility();
  loadFormats();
})();
