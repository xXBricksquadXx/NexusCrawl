import inspect
import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import Request, CivicItem

class CivicAuditSpider(BaseSpider):
    name = "foia_hunter" 
    start_urls = [] 
    def __init__(self):
        self.visited_urls = set() 
    async def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        links = tree.css('a')
        async with httpx.AsyncClient(timeout=10.0) as client:
            for link in links:
                href = link.attributes.get('href')
                if not href or href.startswith(('javascript:', 'mailto:', '#')):
                    continue
                absolute_url = urljoin(current_url, href)
                if 'download' in absolute_url.lower() or 'file' in absolute_url.lower() or absolute_url.endswith(('.pdf', '.csv', '.xlsx', '.zip')):
                    if absolute_url in self.visited_urls: 
                        continue
                    self.visited_urls.add(absolute_url)
                    try:
                        head_resp = await client.head(absolute_url, follow_redirects=True)
                        content_type = head_resp.headers.get('content-type', '').lower()
                        if 'application/' in content_type or 'text/csv' in content_type:
                            filename = link.text(strip=True) or absolute_url.split('/')[-1]
                            print(f"[FOIA] Target Locked: {filename}")
                            yield CivicItem(
                                url=current_url,
                                title=filename,
                                image_url=absolute_url 
                            )
                    except Exception:
                        pass 
                elif '/oip/' in absolute_url and absolute_url not in self.visited_urls:
                    self.visited_urls.add(absolute_url)
                    print(f"[SCOUT] Navigating deeper: {absolute_url}")
                    yield Request(url=absolute_url, callback=self.parse)