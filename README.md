# NexusCrawl

An asynchronous, dual-transmission data mining and historical archival engine. Built for civic audits, large-scale dataset extraction, and media preservation.

## Architecture

NexusCrawl utilizes a hybrid event loop:

- **HTTPX (Standard Routing):** High-speed, low-overhead async requests for static DOM parsing and HTTP `HEAD` reconnaissance.
- **Playwright (Heavy Routing):** Headless Chromium integration for extracting JavaScript-rendered (React/Angular/Vue) data tables and interactive elements.
- **Pipelines:** Asynchronous file streaming (`aiofiles`) to prevent memory bottlenecks during massive data dumps or video downloads. Includes an Exponential Backoff Retry Middleware to defeat 429/403 rate limits and server drops.

## Spider Matrix

| CLI Name        | Target File               | Primary Function                                                                                                                  | Rendering Engine |
| :-------------- | :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------- | :--------------- |
| `foia_hunter`   | `spiders/civic_spider.py` | Deep-crawling, recursive pagination, and async `HEAD` probes to discover and extract hidden government documents (PDF, CSV, ZIP). | HTTPX            |
| `table_miner`   | `spiders/table_spider.py` | Interacts with the browser to flatten complex 2D JS data grids into structured dictionaries.                                      | Playwright       |
| `media_archive` | `spiders/video_spider.py` | Two-phase deep driller. Scans directories, queues watch pages, and streams high-res `.mp4`/`.webm` binaries.                      | HTTPX            |

## Execution Commands

NexusCrawl is driven entirely via the CLI using `main.py`.

**Run a spider on its default target:**

```powershell
python main.py --spider table_miner
```

### Override the default target with a custom URL:

```powershell
python main.py --spider foia_hunter --url "https://www.justice.gov/oip/foia-library"
```
