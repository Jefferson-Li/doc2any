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
        "自動執行版面偵測 → 混合轉換 → 品質評分，挑出較不跑版的結果。",
      "dropzone.aria": "上傳檔案",
      "dropzone.title": "拖曳檔案到這裡",
      "dropzone.sub": "或點擊選擇 · 最大 50MB",
      "dropzone.clear": "清除檔案",
      "controls.target": "轉成",
      "controls.layout": "版面模式",
      "controls.convert": "開始轉換",
      "controls.uploadFirst": "先上傳檔案",
      "layout.auto": "自動混合（建議）",
      "layout.hybrid": "混合轉換",
      "layout.visual": "視覺保版",
      "layout.editable": "可編輯文字",
      "status.default": "正在分析版面…",
      "status.v1": "Layout Detection 分析中…",
      "status.v2": "Hybrid Conversion 比較候選…",
      "status.v3": "計算 Conversion Quality Score…",
      "status.v4": "輸出最佳結果…",
      "status.e1": "正在解析文字區塊…",
      "status.e2": "重建段落與表格…",
      "status.e3": "對齊圖片位置…",
      "status.e4": "輸出可編輯 Word…",
      "result.default": "轉換完成，版面已盡量保留。",
      "result.visual": "已用視覺保版輸出，版面與原 PDF 對齊。",
      "result.editable": "已輸出可編輯文字（複雜設計稿可能仍有位移）。",
      "result.hybrid": "混合管線完成：已依品質評分選出最佳輸出。",
      "result.download": "下載檔案",
      "quality.title": "轉換品質 Conversion Quality",
      "quality.overall": "Overall",
      "quality.layout": "Layout similarity",
      "quality.text": "Text preservation",
      "quality.image": "Image preservation",
      "quality.align": "Element alignment",
      "quality.structure": "Page structure",
      "quality.meta": "版面：{layout} · 引擎：{mode} · 等級：{grade}",
      "quality.retry": "已自動重試：{from} → {to}",
      "error.convert": "轉換失敗",
      "error.retry": "轉換失敗，請稍後再試",
      "how.title": "轉換管線：偵測 → 混合 → 評分",
      "how.lede": "每個 PDF→Word 都會走完整三步驟，自動選出較佳結果。",
      "how.s1.title": "1. Layout Detection",
      "how.s1.body":
        "判斷掃描／設計稿／多欄／簡單文字，並給出建議模式與信心分數。",
      "how.s2.title": "2. Hybrid Conversion",
      "how.s2.body": "同時評估視覺保版與可編輯重建；版面分數過低會自動重試視覺保版。",
      "how.s3.title": "3. Quality Score",
      "how.s3.body":
        "可解釋指標：Layout / Text / Image / Alignment / Page structure，並輸出 Overall。",
      "formats.title": "支援路徑",
      "formats.loading": "正在讀取引擎狀態…",
      "formats.loReady": "LibreOffice 已就緒。PDF→Word 走偵測→混合→評分管線。",
      "formats.coreReady":
        "PDF→Word 已啟用 Layout Detection → Hybrid → Quality Score。",
      "formats.unavailable": "無法讀取引擎狀態，仍可嘗試上傳轉換。",
      "env.banner": "目前環境：{label}",
      "hint.mode.visual": "視覺保版",
      "hint.mode.editable": "可編輯文字",
      "hint.mode.hybrid": "混合轉換",
      "hint.scanned": "掃描影像 PDF（無文字層，需 OCR 才能可編輯）",
      "hint.complex": "設計稿／多欄絕對定位（如 Canva），文字重建會跑版",
      "hint.designed": "設計稿工具匯出（如 Canva），建議視覺／混合保版",
      "hint.simple": "文字流動版面，可嘗試可編輯或混合轉換",
      "hint.template": "偵測：{reason}（信心 {confidence}）→ 建議「{mode}」",
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
        "Runs Layout Detection → Hybrid Conversion → Quality Score to pick the safer output.",
      "dropzone.aria": "Upload a file",
      "dropzone.title": "Drop a file here",
      "dropzone.sub": "or click to browse · max 50MB",
      "dropzone.clear": "Clear file",
      "controls.target": "Convert to",
      "controls.layout": "Layout mode",
      "controls.convert": "Convert",
      "controls.uploadFirst": "Upload a file first",
      "layout.auto": "Auto hybrid (recommended)",
      "layout.hybrid": "Hybrid conversion",
      "layout.visual": "Visual fidelity",
      "layout.editable": "Editable text",
      "status.default": "Analyzing layout…",
      "status.v1": "Layout Detection…",
      "status.v2": "Hybrid Conversion comparing candidates…",
      "status.v3": "Computing Conversion Quality Score…",
      "status.v4": "Exporting the best result…",
      "status.e1": "Parsing text blocks…",
      "status.e2": "Rebuilding paragraphs & tables…",
      "status.e3": "Aligning images…",
      "status.e4": "Exporting editable Word…",
      "result.default": "Done. Layout preserved as much as possible.",
      "result.visual": "Exported with visual fidelity—aligned to the original PDF.",
      "result.editable":
        "Editable text exported (complex designs may still shift).",
      "result.hybrid": "Hybrid pipeline finished—best scored output selected.",
      "result.download": "Download",
      "quality.title": "Conversion Quality",
      "quality.overall": "Overall",
      "quality.layout": "Layout similarity",
      "quality.text": "Text preservation",
      "quality.image": "Image preservation",
      "quality.align": "Element alignment",
      "quality.structure": "Page structure",
      "quality.meta": "Layout: {layout} · Engine: {mode} · Grade: {grade}",
      "quality.retry": "Auto-retried: {from} → {to}",
      "error.convert": "Conversion failed",
      "error.retry": "Conversion failed. Please try again.",
      "how.title": "Pipeline: Detect → Hybrid → Score",
      "how.lede": "Every PDF→Word run follows three steps and picks the better result.",
      "how.s1.title": "1. Layout Detection",
      "how.s1.body":
        "Classifies scanned / designed / multi-column / simple text with a confidence score.",
      "how.s2.title": "2. Hybrid Conversion",
      "how.s2.body":
        "Compares visual fidelity vs editable rebuild; auto-retries visual if layout score collapses.",
      "how.s3.title": "3. Quality Score",
      "how.s3.body":
        "Explainable metrics: Layout / Text / Image / Alignment / Page structure → Overall.",
      "formats.title": "Supported routes",
      "formats.loading": "Loading engine status…",
      "formats.loReady":
        "LibreOffice is ready. PDF→Word uses detect → hybrid → score.",
      "formats.coreReady":
        "PDF→Word pipeline: Layout Detection → Hybrid Conversion → Quality Score.",
      "formats.unavailable":
        "Could not load engine status. You can still try converting.",
      "env.banner": "Environment: {label}",
      "hint.mode.visual": "Visual",
      "hint.mode.editable": "Editable text",
      "hint.mode.hybrid": "Hybrid",
      "hint.scanned": "Scanned image PDF (no text layer—OCR needed for editable text)",
      "hint.complex":
        "Designed / multi-column absolute layout (e.g. Canva)—text rebuild will break",
      "hint.designed": "Design-tool export (e.g. Canva)—prefer visual / hybrid",
      "hint.simple": "Flowing text layout—editable or hybrid may work",
      "hint.template": "Detected: {reason} (confidence {confidence}) → recommend “{mode}”",
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
  const qualityCard = document.getElementById("qualityCard");
  const qualityGrade = document.getElementById("qualityGrade");
  const qualityOverall = document.getElementById("qualityOverall");
  const scoreLayout = document.getElementById("scoreLayout");
  const scoreText = document.getElementById("scoreText");
  const scoreImage = document.getElementById("scoreImage");
  const scoreAlign = document.getElementById("scoreAlign");
  const scoreStructure = document.getElementById("scoreStructure");
  const barLayout = document.getElementById("barLayout");
  const barText = document.getElementById("barText");
  const barImage = document.getElementById("barImage");
  const barAlign = document.getElementById("barAlign");
  const barStructure = document.getElementById("barStructure");
  const qualityMeta = document.getElementById("qualityMeta");
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
    if (data.is_scanned || data.layout_type === "scanned") return "hint.scanned";
    if (data.layout_type === "designed") return "hint.designed";
    if (data.complex_layout || data.layout_type === "complex") return "hint.complex";
    return "hint.simple";
  }

  function modeLabelKey(mode) {
    if (mode === "visual") return "hint.mode.visual";
    if (mode === "hybrid") return "hint.mode.hybrid";
    return "hint.mode.editable";
  }

  function renderAnalyzeHint() {
    if (!lastAnalyze || !selectedFile || extOf(selectedFile.name) !== "pdf") {
      return;
    }
    const mode = lastAnalyze.recommended_mode || "hybrid";
    const reason = t(analyzeReasonKey(lastAnalyze));
    const confidence = Math.round((lastAnalyze.confidence || 0) * 100);
    layoutHint.textContent = t("hint.template")
      .replace("{reason}", reason)
      .replace("{confidence}", `${confidence}%`)
      .replace("{mode}", t(modeLabelKey(mode)));
    layoutHint.classList.remove("hidden");
  }

  function hideQuality() {
    if (qualityCard) qualityCard.classList.add("hidden");
  }

  function showQualityFromHeaders(headers) {
    if (!qualityCard) return;
    const overall = headers.get("X-Doc2Any-Score");
    if (!overall) {
      hideQuality();
      return;
    }
    const grade = headers.get("X-Doc2Any-Grade") || "-";
    const layout = Number(
      headers.get("X-Doc2Any-Score-Layout-Similarity") ||
        headers.get("X-Doc2Any-Score-Layout") ||
        0
    );
    const text = Number(
      headers.get("X-Doc2Any-Score-Text-Preservation") ||
        headers.get("X-Doc2Any-Score-Text") ||
        0
    );
    const image = Number(headers.get("X-Doc2Any-Score-Image-Preservation") || 0);
    const align = Number(headers.get("X-Doc2Any-Score-Element-Alignment") || 0);
    const structure = Number(headers.get("X-Doc2Any-Score-Page-Structure") || 0);
    const layoutType = headers.get("X-Doc2Any-Layout-Type") || "-";
    const modeUsed = headers.get("X-Doc2Any-Mode-Used") || "-";

    qualityGrade.textContent = grade;
    qualityOverall.textContent = overall;
    scoreLayout.textContent = String(layout);
    scoreText.textContent = String(text);
    scoreImage.textContent = String(image);
    scoreAlign.textContent = String(align);
    scoreStructure.textContent = String(structure);
    barLayout.style.width = `${Math.max(0, Math.min(100, layout))}%`;
    barText.style.width = `${Math.max(0, Math.min(100, text))}%`;
    barImage.style.width = `${Math.max(0, Math.min(100, image))}%`;
    barAlign.style.width = `${Math.max(0, Math.min(100, align))}%`;
    barStructure.style.width = `${Math.max(0, Math.min(100, structure))}%`;
    qualityMeta.textContent = t("quality.meta")
      .replace("{layout}", layoutType)
      .replace("{mode}", modeUsed)
      .replace("{grade}", grade);
    qualityCard.classList.remove("hidden");

    // Enrich meta from full report when available
    const reportUrl = headers.get("X-Doc2Any-Report");
    if (reportUrl) {
      fetch(reportUrl)
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (!data) return;
          if (data.retry) {
            qualityMeta.textContent =
              t("quality.meta")
                .replace("{layout}", layoutType)
                .replace("{mode}", modeUsed)
                .replace("{grade}", grade) +
              " · " +
              t("quality.retry")
                .replace("{from}", data.retry.from_mode)
                .replace("{to}", data.retry.to_mode);
          }
        })
        .catch(() => {});
    }
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
    hideQuality();
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
    hideQuality();
    statusEl.classList.remove("hidden");
    convertBtn.disabled = true;

    const usePipelineMsgs =
      layoutMode.value !== "editable" || targetFormat.value === "docx";
    const messages = usePipelineMsgs
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
        const used = (res.headers.get("X-Doc2Any-Mode-Used") || "").toLowerCase();
        if (used === "editable") resultNote.textContent = t("result.editable");
        else if (used === "visual") resultNote.textContent = t("result.visual");
        else resultNote.textContent = t("result.hybrid");
      }
      showQualityFromHeaders(res.headers);
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
