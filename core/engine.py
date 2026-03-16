import inspect
import asyncio
import httpx
from playwright.async_api import async_playwright 
from pydantic import BaseModel  
from models import Request, CivicItem, TableRowItem, VideoItem
from core.middleware import UserAgentMiddleware, RetryMiddleware
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
        self.pw = None
        self.browser = None
        self.retry_middleware = RetryMiddleware(max_retries=3)

    async def start(self):
        print(f"[ENGINE] Starting crawl for spider: {self.spider.name}")
        default_render_js = getattr(self.spider, 'render_js', False)
        
        for url in self.spider.start_urls:
            await self.queue.put(Request(url=url, callback=self.spider.parse, render_js=default_render_js))
            
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            workers = [asyncio.create_task(self.worker(client)) for _ in range(self.semaphore._value)]
            await self.queue.join()  
            
            for w in workers:
                w.cancel() 
                
        await self.browser.close()
        await self.pw.stop()
        print(f"[ENGINE] Crawl complete. Extracted {self.items_scraped_count} items.")

    async def worker(self, client: httpx.AsyncClient):
        while True:
            request = await self.queue.get()
            async with self.semaphore:
                try:
                    headers = self.middleware.process_request({})
                    
                    # 1. Fetch HTML (Playwright vs HTTPX)
                    if request.render_js:
                        print(f"[PLAYWRIGHT] Booting headless tab for: {request.url}")
                        page = await self.browser.new_page(extra_http_headers=headers)
                        response = await page.goto(request.url, wait_until="networkidle", timeout=30000)
                        
                        if hasattr(self.spider, 'interact_with_page'):
                            await self.spider.interact_with_page(page)
                            
                        html = await page.content()
                        status_code = response.status if response else 0
                        await page.close()
                        print(f"[FETCH-JS] [{status_code}] {request.url}")
                    else:
                        response = await self.retry_middleware.execute_with_retry(
                            request=request, 
                            client=client, 
                            headers=headers
                        )
                        html = response.text
                        print(f"[FETCH-HTTPX] [{response.status_code}] {request.url}")

                    # 2. Execute Callback (The Async Patch)
                    result = request.callback(html, request.url)
                    
                    # Dynamically process the output based on how the spider yielded it
                    spider_output = []
                    if inspect.isasyncgen(result):
                        spider_output = [item async for item in result]
                    elif inspect.iscoroutine(result):
                        res = await result
                        if res: spider_output = res
                    else:
                        if result: spider_output = result

                    # 3. Route Output to Queues/Pipelines
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