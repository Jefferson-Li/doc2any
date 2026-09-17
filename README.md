# Doc2Any

**Layout-Aware Document Transformation Engine**  
版面感知的文件轉換引擎

> Doc2Any doesn’t simply convert documents.  
> It **analyzes** the document, **chooses** a conversion strategy, and **evaluates** the quality of the result.

PDF → Word 對複雜設計稿（如 Canva／多欄履歷）走 **Layout Detection → Hybrid Conversion → Quality Score**。  
For complex layouts (Canva / multi-column resumes), conversion follows detect → hybrid → score.

Canva Resume 是 **Origin Story / Killer Use Case**，產品目標是更廣的 **Document Transformation**（結構與版面不被破壞的格式轉換）。

---

## Why Doc2Any (vs a PDF toolbox)

| | Doc2Any | Typical PDF platform (e.g. Stirling-PDF) |
| --- | --- | --- |
| Core | Conversion intelligence | PDF operations breadth |
| Focus | Layout-aware transform + quality | Merge / split / OCR / sign / redact / … |
| Differentiator | Detect → Strategy → Convert → Validate | 50+ PDF tools |

We intentionally **do not** compete on merge/split/sign feature count.  
We compete on **conversion quality you can measure**.

---

## Pipeline

```text
Document
   │
   ▼
Layout Detection          (simple / complex / designed / scanned)
   │
   ▼
Strategy Selector         (editable / hybrid / visual)
   │
   ├──────────┬──────────┐
   ▼          ▼          ▼
Editable   Hybrid     Visual
   │          │          │
   └──────────┼──────────┘
              ▼
     Conversion Engine
              │
              ▼
     Quality Validator
              │
              ▼
     Conversion Quality Score
              │
     score too low? ──► auto-retry (prefer visual)
```

### Conversion Quality (explainable)

```text
Conversion Quality
Overall: 93%

Layout similarity       96%
Text preservation       98%
Image preservation     100%
Element alignment       91%
Page structure          94%
```

How metrics are derived:

| Metric | What it measures |
| --- | --- |
| **Layout similarity** | Visual: page-render vs DOCX embedded page images. Editable: overlap + spacing / section heuristics |
| **Text preservation** | Token overlap & coverage (editable), or raster preservation note (visual) |
| **Image preservation** | PDF image count vs DOCX media / page images |
| **Element alignment** | Aspect alignment (visual) or spaced-out / column penalties (editable) |
| **Page structure** | PDF page count vs DOCX sections / shapes |

Full explain payload is in `conversion_report.json` (`GET /api/jobs/{id}/report`).

---

## Features

| 中文 | English |
| --- | --- |
| **PDF → DOCX 管線** | Detect → Hybrid → Score (+ auto-retry) |
| **視覺保版 / 可編輯 / 混合** | Visual / Editable / Hybrid modes |
| **可解釋 Quality Score** | Five metrics + Overall + Grade |
| **環境設定** | development / staging / production |
| **Rate limit + TTL cleanup** | Abuse protection & temp file purge |
| **Docker** | Local / staging / production compose |

---

## Quick start

```bash
cp .env.example .env
./start.sh
```

- App: http://localhost:8000  
- API docs: http://localhost:8000/docs  

UI language: **繁中 / EN** toggle.

### Docker

```bash
# staging
cp .env.staging.example .env.staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml \
  --env-file .env.staging up -d --build

# production
cp .env.production.example .env.production
docker compose -f docker-compose.yml -f docker-compose.production.yml \
  --env-file .env.production up -d --build
```

---

## Configuration

Prefix: `DOC2ANY_`. See `.env.example`, `.env.staging.example`, `.env.production.example`.

| Variable | Meaning | Default |
| --- | --- | --- |
| `DOC2ANY_ENV` | development / staging / production | `development` |
| `DOC2ANY_DATA_DIR` | Data root (`uploads/`, `outputs/`) | `backend/` |
| `DOC2ANY_MAX_UPLOAD_MB` | Upload cap | `50` |
| `DOC2ANY_RATE_LIMIT_PER_MINUTE` | Convert rate / IP | `20` |
| `DOC2ANY_FILE_TTL_SECONDS` | Job folder TTL | `3600` |
| `DOC2ANY_CORS_ORIGINS` | Allowed origins | `*` |

Jobs land in `{DATA_DIR}/outputs/<job-id>/` (source + result + `conversion_report.json`).

---

## Layout modes (PDF → Word)

| Mode | Behavior |
| --- | --- |
| **Auto / Hybrid** | Detect layout, score visual + editable, pick winner; retry visual if layout collapses |
| **Visual** | Full-page images in Word (layout-safe) |
| **Editable** | Text reconstruction (best for simple single-column docs) |

---

## Project structure

```
Dockerfile
docker-compose.yml
docker-compose.staging.yml
docker-compose.production.yml
backend/app/
  main.py
  config.py
  rate_limit.py
  cleanup.py
  converters/
    layout_detect.py      # Layout Detection
    pipeline.py           # Hybrid orchestration + retry
    quality.py            # Explainable Quality Score
    engine.py             # Format converters
  static/                 # UI + i18n
```

---

## Product direction (what we will / won’t do)

**Do next:** deeper layout classes, better hybrid region splitting, OCR for scans, benchmarks (Canva PDF → DOCX vs LibreOffice), demo GIF, architecture diagram in repo.

**Don’t:** become a low-end Stirling-PDF clone (merge/split/sign/watermark race). Breadth is their game; **conversion intelligence** is ours.
