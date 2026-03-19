import inspect
import httpx
import asyncio
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from spiders.base import BaseSpider
from models import Request, CivicItem


class CivicAuditSpider(BaseSpider):
    name = "foia_hunter"
    start_urls = []

    def __init__(self, max_depth=2):
        self.visited_urls = set()
        self.url_depths = {}
        self.max_depth = max_depth
        self.allowed_domain = None

    async def parse(self, html: str, current_url: str):
        if not self.allowed_domain:
            self.allowed_domain = urlparse(current_url).netloc.replace("www.", "")
        current_depth = self.url_depths.get(current_url, 0)
        print(f"\n[BREACH INITIATED] Target: {current_url} | Depth: {current_depth}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type
                    in ["image", "media", "font", "stylesheet"]
                    else route.continue_()
                ),
            )
            try:
                await page.goto(
                    current_url, wait_until="domcontentloaded", timeout=60000
                )
                viewstate_count = await page.locator(
                    "input[name='__VIEWSTATE']"
                ).count()
                if viewstate_count > 0:
                    print(f"  -> [BYPASS] ASP.NET __VIEWSTATE intercepted.")
                csrf_count = await page.locator("meta[name='csrf-token']").count()
                if csrf_count > 0:
                    token = await page.locator("meta[name='csrf-token']").get_attribute(
                        "content"
                    )
                    print(f"  -> [BYPASS] CSRF Token intercepted: {str(token)[:10]}...")
                links = await page.locator("a").element_handles()
                for link in links:
                    href = await link.get_attribute("href")
                    if not href or href.startswith(("javascript:void", "mailto:", "#")):
                        continue
                    title = await link.inner_text()
                    title = title.strip() if title else "Unnamed_Document"
                    page_slug = current_url.strip("/").split("/")[-1]
                    page_slug = page_slug if len(page_slug) >= 3 else "root_page"
                    generic_terms = ["here", "minutes", "agenda", "download", "link"]
                    if title.lower() in generic_terms or len(title) < 5:
                        filename = f"{page_slug}_{title}"
                    else:
                        filename = title
                    absolute_url = urljoin(current_url, href)
                    parsed_url = urlparse(absolute_url)
                    domain = parsed_url.netloc.replace("www.", "")
                    if domain != self.allowed_domain:
                        continue
                    if (
                        "download" in absolute_url.lower()
                        or "file" in absolute_url.lower()
                        or "/wp-content/uploads/" in absolute_url.lower()
                        or absolute_url.lower().endswith(
                            (".pdf", ".csv", ".xlsx", ".zip")
                        )
                    ):
                        if absolute_url not in self.visited_urls:
                            self.visited_urls.add(absolute_url)
                            filename = title or absolute_url.split("/")[-1]
                            print(f"  -> [FOIA] Target Locked: {filename[:50]}...")
                            yield CivicItem(
                                url=current_url, title=filename, image_url=absolute_url
                            )
                    elif "javascript:__doPostBack" in href:
                        print(
                            f"  -> [TRIGGER] ASP.NET PostBack mechanism discovered: {title}"
                        )
                    elif absolute_url not in self.visited_urls:
                        if (
                            "tribe-bar-date" in absolute_url.lower()
                            or "?month=" in absolute_url.lower()
                        ):
                            continue
                        if current_depth < self.max_depth:
                            self.visited_urls.add(absolute_url)
                            self.url_depths[absolute_url] = current_depth + 1
                            print(
                                f"  -> [SCOUT] Traversing deeper (Depth {current_depth + 1}): {absolute_url}"
                            )
                            yield Request(url=absolute_url, callback=self.parse)
            except Exception as e:
                print(f"[ERROR] Playwright breach failed on {current_url}: {e}")
            finally:
                await browser.close()
