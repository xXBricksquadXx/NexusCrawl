# NexusCrawl

An asynchronous, dual-transmission data mining and historical archival engine. Built for civic audits, large-scale dataset extraction, and media preservation.

## Architecture

NexusCrawl utilizes a hybrid event loop:

- **HTTPX (Standard Routing):** High-speed, low-overhead async requests for static DOM parsing.
- **Playwright (Heavy Routing):** Headless Chromium integration for extracting JavaScript-rendered (React/Angular/Vue) data tables and interactive elements.
- **Pipelines:** Asynchronous file streaming (`aiofiles`) to prevent memory bottlenecks during massive data dumps or video downloads. Includes an Exponential Backoff Retry Middleware to defeat basic 429/403 rate limits.

## Spider Matrix

| CLI Name        | Target File               | Primary Function                                                  | Rendering Engine |
| :-------------- | :------------------------ | :---------------------------------------------------------------- | :--------------- |
| `book_archive`  | `spiders/civic_spider.py` | Deep-crawling, pagination, hierarchical HTML extraction.          | HTTPX            |
| `table_miner`   | `spiders/table_spider.py` | Flattening complex 2D JS data grids into structured dictionaries. | Playwright       |
| `media_archive` | `spiders/video_spider.py` | Binary asset discovery and chunked media downloading.             | HTTPX            |

## Execution Commands

NexusCrawl is driven entirely via the CLI using `main.py`.

**Run a spider on its default target:**

```powershell
python main.py --spider table_miner
```

### Override the default target with a custom URL:

```powershell
python main.py --spider media_archive --url "[https://target-video-site.gov/media](https://target-video-site.gov/media)"
```
