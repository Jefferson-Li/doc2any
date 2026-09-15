# Doc2Any

上傳任意格式、轉成指定格式的本機網站。PDF → Word 使用版面重建引擎，盡量保留段落、表格與圖片位置。

## 功能

- **PDF → DOCX**：以 `pdf2docx` 重建版面（段落 / 表格 / 圖片）
- **圖片互轉**：PNG / JPG / WebP / PDF
- **DOCX → HTML / TXT**：本機解析
- **LibreOffice（可選）**：安裝後可擴充 DOC / PPTX / XLSX / DOCX↔PDF 等保真路徑

> 掃描版 PDF 需先 OCR；多欄、公式、複雜浮動排版無法保證像素級一致。

## 快速開始

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

瀏覽器開啟：http://localhost:8000

API 文件：http://localhost:8000/docs

### 可選：安裝 LibreOffice（擴充 Office 轉換）

```bash
# macOS
brew install --cask libreoffice
```

## 使用方式

1. 拖曳或選擇檔案（最大 50MB）
2. 選擇目標格式（PDF 預設建議轉 DOCX）
3. 點「開始轉換」後下載結果

檔案只在本機處理，不會上傳到第三方雲端。

## 專案結構

```
backend/
  app/
    main.py              # FastAPI + 靜態網站
    converters/engine.py # 轉換路由與引擎
    static/              # 前端 UI
  requirements.txt
```
