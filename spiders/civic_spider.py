import inspect
import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from spiders.base import BaseSpider
from models import Request, CivicItem


class CivicAuditSpider(BaseSpider):
    name = "foia_hunter"
    start_urls = []

    def __init__(self, max_depth=3):
        self.visited_urls = set()
        self.url_depths = {}
        self.max_depth = max_depth
        self.allowed_domain = None

    async def parse(self, html: str, current_url: str):
        if not self.allowed_domain:
            self.allowed_domain = urlparse(current_url).netloc.replace("www.", "")
        current_depth = self.url_depths.get(current_url, 0)
        tree = HTMLParser(html)
        links = tree.css("a")
        async with httpx.AsyncClient(timeout=10.0) as client:
            for link in links:
                href = link.attributes.get("href")
                if not href or href.startswith(("javascript:", "mailto:", "#")):
                    continue
                absolute_url = urljoin(current_url, href)
                parsed_url = urlparse(absolute_url)
                domain = parsed_url.netloc.replace("www.", "")
                if domain != self.allowed_domain:
                    continue
                if (
                    "download" in absolute_url.lower()
                    or "file" in absolute_url.lower()
                    or "/wp-content/uploads/" in absolute_url.lower()
                    or absolute_url.endswith((".pdf", ".csv", ".xlsx", ".zip"))
                ):
                    if absolute_url in self.visited_urls:
                        continue
                    self.visited_urls.add(absolute_url)
                    try:
                        head_resp = await client.head(
                            absolute_url, follow_redirects=True
                        )
                        content_type = head_resp.headers.get("content-type", "").lower()
                        if "application/" in content_type or "text/csv" in content_type:
                            filename = (
                                link.text(strip=True) or absolute_url.split("/")[-1]
                            )
                            print(f"[FOIA] Target Locked: {filename}")
                            yield CivicItem(
                                url=current_url, title=filename, image_url=absolute_url
                            )
                    except Exception:
                        pass
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
                            f"[SCOUT] Navigating deeper (Depth {current_depth + 1}): {absolute_url}"
                        )
                        yield Request(url=absolute_url, callback=self.parse)
