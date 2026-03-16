![NexusCrawl Banner](public/banner.png)

---

# NexusCrawl

An asynchronous, dual-transmission data mining, historical archival, and web reconnaissance engine. Built for civic audits, large-scale dataset extraction, deep media preservation, and source code cloning.

---

## Core Architecture

NexusCrawl utilizes a highly concurrent, hybrid event loop:

- **HTTPX (Standard Routing):** High-speed, low-overhead async requests for static DOM parsing and HTTP `HEAD` reconnaissance.
- **Playwright (Heavy Routing):** Headless Chromium integration for extracting JavaScript-rendered (React/Angular/Vue) data tables, interactive DOM elements, and executing client-side scripts before extraction.

### Resiliency & Data Pipelines

- **Exponential Backoff Shield:** A built-in `RetryMiddleware` that intercepts HTTP `429` (Rate Limit) and HTTP `403` (Forbidden) server drops, pauses the specific worker, and gracefully retries the connection without killing the primary crawl.
- **Asynchronous File Streaming:** Utilizes `aiofiles` to prevent desktop RAM bottlenecks. Data is streamed directly to disk whether it is a `.jsonl` dictionary string, a cloned `.css` file, or a massive binary.
- **Dual-Routing SQL Exporter:** Automatically routes extracted datasets into a local `nexus_database.db` SQLite database. It handles both raw web payloads (JSON row data) and refined intelligence models (like parsed budget lines and meeting votes) simultaneously.
- **Structural PDF Exploiter:** An offline, regex-hardened parser (`pdfplumber`) that bypasses phantom gridlines and watermark interference to rip tabular financial data and unstructured meeting minutes directly from downloaded government PDFs.
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

## 2. Install Headless Chromium (Required for Playwright)

```bash
playwright install chromium
```

## 3. Install FFmpeg (Required for Media Archival/Stream Stitching)

_Windows (via winget)_:

```bash
winget install Gyan.FFmpeg
```

---

# Execution Commands

NexusCrawl is driven entirely via the CLI using `main.py`.

## Run a spider on its default hardcoded target

```bash
python main.py --spider table_miner
```

## Override the default target with a custom URL

```bash
python main.py --spider foia_hunter --url "https://www.justice.gov/oip/foia-library"
```

## Execute a Web Reconnaissance clone

```bash
python main.py --spider web_recon --url "https://target-domain.com"
```

## Extract Intelligence from Downloaded PDFs (Offline Parsing)

Run the mass-exploitation parser across all PDFs in the `/media` directory to extract financial ledgers and meeting minutes:

```bash
python parsers/pdf_parser.py
```

_Target a specific document to verify the layout heuristics before executing a mass extraction:_

```bash
python parsers/pdf_parser.py --file "FY 24-25 Budget.pdf"
```

## Query the Intelligence Vault (Mass Text Search)

_Scan the extracted text of all downloaded documents simultaneously for specific keywords, returning a 60-character context window around the target phrase_:

```bash
python search_intel.py --keyword "Opioid"
```

```bash
python search_intel.py --keyword "Approved"
```

## Export Intelligence to CSV for Visualization

Dump the relational SQLite data into flat `.csv` files for Excel/Tableau visualization and financial delta calculations:

```bash
python export_csv.py
```

_(This generates financial_audit_export.csv and raw_text_export.csv in the root directory)._

---

# Data Output Structure

Running the framework will automatically generate the following local directories based on the pipelines engaged:

```text
/nexus_database.db
/parsed_intel.db
/civic_audit_data.jsonl
/media/
/recon_vault/
```

### `/nexus_database.db`

Relational SQLite database containing structured, queryable extractions:

- `civic_records` & `table_records` (Live crawler payloads)

- `budget_items` & `meeting_votes` (Refined intelligence extracted from PDFs)

### `/parsed_intel.db`

Secondary SQLite database housing bulk analytical data ripped from documents:

- `extracted_tables` (Raw tabular matrices wrapped in JSON)

- `extracted_text` (Raw, searchable paragraph text for policy and agenda tracking)

/civic_audit_data.jsonl

### `/civic_audit_data.jsonl`

Flat JSON Lines file for structured table data and text extraction.

### `/media/`

Stores binary files such as:

- Images
- Videos
- PDFs
- CSV datasets
- `/media/streams/`: High-resolution `.mp4` files intercepted and stitched via `yt-dlp`.

### `/recon_vault/`

Cloned website source code organized by target domain and file type:

```
/recon_vault
    /domain-name
        /html
        /css
        /js
```

---

# Operational Use Cases

NexusCrawl is designed to automate the heavy lifting of civic audits and web reconnaissance. Here is how the pipelines stack to create actionable intelligence:

### 1. The Fiscal Audit (FOIA Hunter + PDF Exploiter)

**Objective:** Compare year-over-year county budget allocations without manually reading hundreds of pages.
**Execution:**

1. Run `foia_hunter` against the local government portal to strip all hidden PDFs (Budgets, Strategic Plans, Minutes).
2. Execute the `pdf_parser.py` offline to rip the unstructured gridlines and dump the raw account codes and dollar amounts into the SQLite database.
3. Export the database to CSV to instantly visualize anomalies or missing funds between FY24 and FY25.

### 2. The Legislative Tracker (Intelligence Search)

**Objective:** Track the timeline of a specific contract, grant, or committee vote across a massive dump of unstandardized meeting minutes.
**Execution:**

1. Run the mass extraction parser to dump the raw text of all PDFs into `parsed_intel.db`.
2. Execute `search_intel.py --keyword "Agri-Park"` to instantly pull every motion, second, and approval related to the project, tagged with the exact source file and page number.

### 3. The Digital Preservation (Web Recon + Media Archive)

**Objective:** Clone a target's web infrastructure or archive streaming evidence before it is taken offline.
**Execution:**

1. Run `web_recon` to clone the HTML/CSS/JS architecture locally.
2. Run `media_archive` to intercept the HLS/Blob streams via `yt-dlp` and stitch them into permanent local `.mp4` files.
