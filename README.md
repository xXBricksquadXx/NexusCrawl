![NexusCrawl Banner](public/banner.png)

---

# NexusCrawl

An asynchronous, dual-transmission data mining, historical archival, and web reconnaissance engine. Built for civic audits, large-scale dataset extraction, deep media preservation, and offline AI-driven intelligence structuring.

---

## Core Architecture

NexusCrawl utilizes a highly concurrent, hybrid event loop:

- **HTTPX (Standard Routing):** High-speed, low-overhead async requests for static DOM parsing and HTTP `HEAD` reconnaissance.
- **Playwright (Heavy Routing):** Headless Chromium integration for extracting JavaScript-rendered (React/Angular/Vue) data tables, interactive DOM elements, and executing client-side scripts before extraction.

### Resiliency & Data Pipelines

- **Exponential Backoff Shield:** A built-in `RetryMiddleware` that intercepts HTTP `429` (Rate Limit) and HTTP `403` (Forbidden) server drops, pauses the specific worker, and gracefully retries the connection without killing the primary crawl.
- **Asynchronous File Streaming:** Utilizes `aiofiles` to prevent desktop RAM bottlenecks. Data is streamed directly to disk whether it is a `.jsonl` dictionary string, a cloned `.css` file, or a massive binary.
- **Dual-Routing SQL Exporter:** Automatically routes extracted datasets into a local `nexus_database.db` SQLite database. It handles both raw web payloads (JSON row data) and refined intelligence models (parsed budget lines and meeting votes) simultaneously.
- **Structural PDF Exploiter & OCR Fallback:** An offline, regex-hardened parser (`pdfplumber`) that rips tabular financial data from digital PDFs. If a document is a scanned "ghost" image, it automatically routes the file through a local Tesseract/Poppler OCR pipeline to force text extraction.
- **Offline LLM Structuring:** Utilizes local, offline AI models (via Ollama) and `instructor` to read chaotic OCR text dumps and reconstruct them into mathematically perfect, structured Pydantic models (e.g., identifying specific parliamentary votes, motions, and financial impacts).
- **Stream Interceptor:** Offloads HLS/Blob streams to a background `yt-dlp` threading pipeline, automatically utilizing FFmpeg to decrypt and stitch streaming video chunks into native `.mp4` files.

---

# The Spider Matrix

| CLI Name        | Target File               | Primary Function                                                                                                                  | Rendering Engine   | Output Pipeline      |
| --------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------- |
| `foia_hunter`   | `spiders/civic_spider.py` | Deep-crawling, recursive pagination, and async `HEAD` probes to discover and extract hidden government documents (PDF, CSV, ZIP). | HTTPX              | `AsyncMediaPipeline` |
| `table_miner`   | `spiders/table_spider.py` | Takes control of the browser to flatten complex, paginated 2D JS data grids into structured dictionaries.                         | Playwright         | `JsonLinesPipeline`  |
| `media_archive` | `spiders/video_spider.py` | Two-phase deep driller. Scans directories, queues watch pages, and streams high-res `.mp4` / `.webm` binaries.                    | HTTPX              | `AsyncMediaPipeline` |
| `web_recon`     | `spiders/recon_spider.py` | Navigates to a target, executes client-side scripts, and clones the rendered HTML, CSS, and JS into a local repository.           | Playwright + HTTPX | `SourceCodePipeline` |

---

# Installation & Setup

## 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 2. Install Headless Chromium & FFmpeg

Required for Playwright rendering and media stream stitching. Run these in an Administrator PowerShell:

```bash
playwright install chromium
winget install Gyan.FFmpeg
```

## 3. Install the OCR Engine (Tesseract & Poppler)

To process scanned, non-digital PDFs, NexusCrawl requires Tesseract and Poppler binaries locally.

### Global Tesseract Install (Admin PowerShell)

```powershell
winget install -e --id UB-Mannheim.TesseractOCR
```

### Local Poppler Setup

- Download the latest Poppler Windows release zip from `oschwartz10612/poppler-windows`.
- Extract the core folder directly into the root of this repository and rename it to `poppler`.
- Ensure the path `poppler/Library/bin/pdftoppm.exe` exists.

## 4. Install Offline AI Engine (Ollama)

Required for zero-cost, localized NLP and structured data extraction.

```powershell
irm https://ollama.com/install.ps1 | iex
ollama run llama3.2
```

---

# Execution Commands

NexusCrawl is driven entirely via the CLI using `main.py` and modular scripts.

## The Crawler Operations

Run a spider on its default hardcoded target:

```bash
python main.py --spider table_miner
```

Override the default target with a custom URL:

```bash
python main.py --spider foia_hunter --url "https://gilescountytn.gov/"
```

---

## The Intelligence Operations

### 1. Extract Raw Intelligence & Budgets from PDFs

```bash
python parsers/pdf_parser.py
```

### 2. Detonate the NLP Nuke (Structured AI Extraction)

```bash
python scripts/nlp_nuke.py
```

### 3. Generate an Executive Audit Briefing

```bash
# Summarize a specific document
python scripts/intel_summary.py --file "Minutes_3b8527.pdf"

# Generate a global briefing
python scripts/intel_summary.py
```

### 4. Export Intelligence to CSV

```bash
python scripts/export_csv.py
```

---

# Data Output Structure

```
/nexus_database.db
/parsed_intel.db
/civic_audit_data.jsonl
/media/
/recon_vault/
```

## `/nexus_database.db`

Relational SQLite database containing structured, queryable extractions:

- `civic_records` & `table_records` (Live crawler payloads)
- `budget_items` & `meeting_votes` (Refined intelligence extracted from PDFs)

## `/parsed_intel.db`

Secondary SQLite database housing bulk analytical data:

- `extracted_tables` (Raw tabular matrices wrapped in JSON)
- `extracted_text` (Raw, searchable paragraph text)

## `/media/`

Stores downloaded binary files (Images, Videos, PDFs).

## `/recon_vault/`

Cloned website source code organized by target domain and file type.

---

# Operational Use Cases

## 1. The Fiscal Audit (FOIA Hunter + PDF Exploiter)

**Objective:** Compare year-over-year county budget allocations.

**Execution:**

- Run `foia_hunter` against a government portal.
- Execute `pdf_parser.py` to extract financial data.
- Export to CSV for visualization.

## 2. The Parliamentary Extractor (The NLP Nuke)

**Objective:** Track voting records across meeting minutes.

**Execution:**

- Extract raw text into `parsed_intel.db`.
- Run `nlp_nuke.py` with Ollama.
- Output structured JSON of motions and votes.

## 3. The Executive Synthesizer (Intel Summary)

**Objective:** Generate high-level summaries of operations and finances.

**Execution:**

- Run `intel_summary.py`.
- Output `Executive_Audit_Briefing.md`.

## 4. The Digital Preservation (Web Recon + Media Archive)

**Objective:** Clone infrastructure and archive media before removal.

**Execution:**

- Run `web_recon` for site cloning.
- Run `media_archive` for stream capture and `.mp4` generation.

---
