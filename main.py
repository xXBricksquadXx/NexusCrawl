import asyncio
import argparse
from core.engine import Engine
from spiders.civic_spider import CivicAuditSpider
from spiders.video_spider import MediaArchiveSpider
from spiders.table_spider import TableDataSpider
SPIDER_REGISTRY = {
    "foia_hunter": CivicAuditSpider,
    "media_archive": MediaArchiveSpider,
    "table_miner": TableDataSpider
}
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusCrawl: Async Data Mining & Archival Engine")
    parser.add_argument(
        "--spider", 
        type=str, 
        required=True, 
        choices=SPIDER_REGISTRY.keys(),
        help="The name of the spider to execute."
    )
    parser.add_argument(
        "--url", 
        type=str, 
        help="Inject a target URL, overriding the spider's default start_urls."
    )
    args = parser.parse_args()
    spider_class = SPIDER_REGISTRY[args.spider]
    spider = spider_class()
    if args.url:
        print(f"[CLI] Overriding default URL with: {args.url}")
        spider.start_urls = [args.url]
    engine = Engine(spider=spider, max_concurrency=3)
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Crawl aborted by user.")