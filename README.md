# Doc2Any

本機文件轉換網站：上傳任意格式、轉成指定格式。  
A local document converter: upload any format and convert to a target format.

PDF → Word 對複雜設計稿（如 Canva／多欄履歷）預設使用**視覺保版**，版面與原檔對齊。  
For complex layouts (Canva / multi-column resumes), PDF → Word defaults to **visual fidelity** so the page matches the original.

---

## 功能 / Features

| 中文 | English |
| --- | --- |
| **PDF → DOCX（視覺保版）**：逐頁高清渲染，適合 Canva／履歷 | **PDF → DOCX (visual)**: page-as-image; best for Canva / resumes |
| **PDF → DOCX（可編輯）**：單欄文字重建；掃描件需先 OCR | **PDF → DOCX (editable)**: text rebuild for simple docs; scans need OCR |
| **圖片互轉**：PNG / JPG / WebP / PDF | **Image conversion**: PNG / JPG / WebP / PDF |
| **DOCX → HTML / TXT**：本機解析 | **DOCX → HTML / TXT**: local parsing |
| **LibreOffice（可選）**：擴充 DOC / PPTX / XLSX / DOCX↔PDF | **LibreOffice (optional)**: more Office routes |

> Canva 履歷跑版通常**不是 OCR**，而是多欄絕對定位無法用流動段落還原。請用「自動／視覺保版」。  
> Layout break on Canva resumes is usually **not OCR**—floating multi-column layout cannot be reconstructed as flowing Word text. Use **Auto / Visual**.

---

## 快速開始 / Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或一鍵啟動 / Or:

```bash
./start.sh
```

- 網站 / App: http://localhost:8000  
- API 文件 / API docs: http://localhost:8000/docs  

網站右上角可切換 **繁體中文 / English**。  
Use the **繁中 / EN** toggle in the top bar.

### 可選：LibreOffice / Optional LibreOffice

```bash
# macOS
brew install --cask libreoffice
```

---

## 使用方式 / How to use

1. 拖曳或選擇檔案（最大 50MB） / Drag or choose a file (max 50MB)  
2. 選擇目標格式（PDF 建議 DOCX） / Pick target format (PDF → DOCX recommended)  
3. PDF→Word 可選版面模式 / For PDF→Word, pick a layout mode  
4. 點「開始轉換」後下載 / Click Convert, then download  

檔案只在本機處理（`backend/outputs/<job-id>/`），不上傳第三方雲端。  
Files stay on your machine (`backend/outputs/<job-id>/`); nothing is sent to a third-party cloud.

---

## 版面模式 / Layout modes (PDF → Word)

| 模式 Mode | 說明 Description |
| --- | --- |
| **自動 Auto** | 偵測 Canva／多欄／掃描後選擇引擎 / Detects Canva, multi-column, or scan |
| **視覺保版 Visual** | 整頁圖像進 Word，幾乎不跑版 / Full-page image in Word; layout-safe |
| **可編輯 Editable** | 重建可選文字；複雜設計可能位移 / Rebuilds selectable text; complex layouts may shift |

---

## 專案結構 / Project structure

```
backend/
  app/
    main.py              # FastAPI + static site
    converters/engine.py # Conversion engines
    static/              # Frontend UI (i18n zh-Hant / en)
  uploads/               # Reserved (unused)
  outputs/               # Upload + convert job folders
  requirements.txt
start.sh                 # One-command launcher
```
