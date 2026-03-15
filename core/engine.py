import asyncio
import httpx
from pydantic import BaseModel  
from models import Request, CivicItem, TableRowItem, VideoItem
from core.middleware import UserAgentMiddleware
from core.pipeline import JsonLinesPipeline, AsyncMediaPipeline
class Engine:
    def __init__(self, spider, max_concurrency=5):
        self.spider = spider
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.middleware = UserAgentMiddleware()
        self.pipeline = JsonLinesPipeline("civic_audit_data.jsonl") 
        self.items_scraped_count = 0 
        self.media_pipeline = AsyncMediaPipeline()
    async def start(self):
        print(f"[ENGINE] Starting crawl for spider: {self.spider.name}")
        for url in self.spider.start_urls:
            await self.queue.put(Request(url=url, callback=self.spider.parse))
        async with httpx.AsyncClient(timeout=10.0) as client:
            workers = [asyncio.create_task(self.worker(client)) for _ in range(self.semaphore._value)]
            await self.queue.join()  
            for w in workers:
                w.cancel() 
        print(f"[ENGINE] Crawl complete. Extracted {self.items_scraped_count} items.")
    async def worker(self, client: httpx.AsyncClient):
        while True:
            request = await self.queue.get()
            async with self.semaphore:
                try:
                    headers = self.middleware.process_request({})
                    response = await client.get(request.url, headers=headers)
                    response.raise_for_status()
                    print(f"[FETCH] [{response.status_code}] {request.url}")
                    spider_output = request.callback(response.text, request.url)
                    if spider_output:
                        for output in spider_output:
                            if isinstance(output, Request):
                                await self.queue.put(output)
                            elif isinstance(output, BaseModel): 
                                await self.pipeline.process_item(output)
                                self.items_scraped_count += 1
                                if getattr(output, 'image_url', None):
                                    await self.media_pipeline.download_image(
                                        media_url=output.image_url, 
                                        filename=output.title
                                    )
                except Exception as e:
                    print(f"[ERROR] Failed {request.url}: {e}")
                finally:
                    self.queue.task_done()