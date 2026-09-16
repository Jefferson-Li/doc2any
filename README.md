# Doc2Any

本機／雲端文件轉換網站：上傳任意格式、轉成指定格式。  
A document converter for local or cloud: upload any format and convert to a target format.

PDF → Word 對複雜設計稿（如 Canva／多欄履歷）預設使用**視覺保版**，版面與原檔對齊。  
For complex layouts (Canva / multi-column resumes), PDF → Word defaults to **visual fidelity**.

---

## 功能 / Features

| 中文 | English |
| --- | --- |
| **PDF → DOCX（視覺保版）**：逐頁高清渲染，適合 Canva／履歷 | **PDF → DOCX (visual)**: page-as-image; best for Canva / resumes |
| **PDF → DOCX（可編輯）**：單欄文字重建；掃描件需先 OCR | **PDF → DOCX (editable)**: text rebuild for simple docs; scans need OCR |
| **圖片互轉**：PNG / JPG / WebP / PDF | **Image conversion**: PNG / JPG / WebP / PDF |
| **環境設定**：development / staging / production | **Environments**: development / staging / production |
| **頻率限制 + 自動清理**：防濫用、定期刪除暫存 | **Rate limit + cleanup**: abuse protection & TTL purge |

> Canva 履歷跑版通常**不是 OCR**。請用「自動／視覺保版」。  
> Canva layout break is usually **not OCR**. Use **Auto / Visual**.

---

## 環境變數 / Configuration

所有變數使用前綴 `DOC2ANY_`。範例檔：

- `.env.example` — 本機開發  
- `.env.staging.example` — 測試環境  
- `.env.production.example` — 正式環境  

| 變數 Variable | 說明 | 預設 Default |
| --- | --- | --- |
| `DOC2ANY_ENV` | `development` / `staging` / `production` | `development` |
| `DOC2ANY_DATA_DIR` | 資料根目錄（其下 `uploads/`、`outputs/`） | `backend/` |
| `DOC2ANY_UPLOAD_DIR` | 上傳目錄（可覆寫） | `{DATA_DIR}/uploads` |
| `DOC2ANY_OUTPUT_DIR` | 轉換暫存目錄（可覆寫） | `{DATA_DIR}/outputs` |
| `DOC2ANY_MAX_UPLOAD_MB` | 上傳大小上限 MB | `50` |
| `DOC2ANY_RATE_LIMIT_PER_MINUTE` | 每 IP 每分鐘轉換次數 | `20` |
| `DOC2ANY_RATE_LIMIT_ANALYZE_PER_MINUTE` | 每 IP 每分鐘分析次數 | `40` |
| `DOC2ANY_FILE_TTL_SECONDS` | 暫存檔保留秒數後自動刪除 | `3600` |
| `DOC2ANY_CLEANUP_INTERVAL_SECONDS` | 清理掃描間隔 | `300` |
| `DOC2ANY_CORS_ORIGINS` | 允許的前端來源（逗號分隔） | `*` |
| `DOC2ANY_PUBLIC_LABEL` | 非 production 時顯示的環境標籤 | 依 ENV |
| `DOC2ANY_DEBUG` | 除錯；production 會強制關閉 | `false` |

路徑範例：

```bash
# 本機
DOC2ANY_DATA_DIR=/Users/you/doc2any-data

# Docker（已內建）
DOC2ANY_DATA_DIR=/data
# → /data/uploads , /data/outputs/<job-id>/
```

---

## 本機快速開始 / Local quick start

```bash
cp .env.example .env
./start.sh
```

或手動：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- App: http://localhost:8000  
- API: http://localhost:8000/docs（production 預設關閉）  

---

## Docker：測試 / 正式環境

### 本機 Docker

```bash
cp .env.example .env
docker compose up -d --build
# http://localhost:8000
```

### Staging（測試）

```bash
cp .env.staging.example .env.staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml \
  --env-file .env.staging up -d --build
# 預設 http://localhost:8001 ，頁面會顯示 Staging 橫幅
```

### Production（正式）

```bash
cp .env.production.example .env.production
# 編輯 DOC2ANY_CORS_ORIGINS=https://你的網域
docker compose -f docker-compose.yml -f docker-compose.production.yml \
  --env-file .env.production up -d --build
# http://localhost:8000 （建議前面再掛 Nginx/Caddy + HTTPS）
```

常用指令：

```bash
docker compose logs -f doc2any
docker compose down
```

---

## 安全與暫存行為 / Security & retention

- **頻率限制**：超過每分鐘上限回傳 `429`  
- **自動清理**：背景任務依 `FILE_TTL_SECONDS` 刪除 `outputs/<job-id>/`  
- **正式環境**：關閉 `/docs`（除非 `DEBUG=true`）、較嚴的 rate limit、建議限制 CORS  

公開部署後，檔案會暫存在**伺服器**磁碟，直到 TTL 到期；請告知使用者隱私政策。

---

## 版面模式 / Layout modes (PDF → Word)

| 模式 Mode | 說明 |
| --- | --- |
| **自動 Auto** | 偵測 Canva／多欄／掃描 |
| **視覺保版 Visual** | 整頁圖像，幾乎不跑版 |
| **可編輯 Editable** | 重建可選文字；複雜設計可能位移 |

---

## 專案結構 / Project structure

```
Dockerfile
docker-compose.yml
docker-compose.staging.yml
docker-compose.production.yml
.env.example
.env.staging.example
.env.production.example
backend/
  app/
    main.py
    config.py              # env settings
    rate_limit.py
    cleanup.py
    converters/engine.py
    static/                # UI + i18n
  requirements.txt
start.sh
```
