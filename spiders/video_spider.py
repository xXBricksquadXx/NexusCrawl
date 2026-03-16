from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import Request, VideoItem

class MediaArchiveSpider(BaseSpider):
    name = "media_archive"
    start_urls = ["https://test-videos.co.uk/"]
    def __init__(self):
        self.visited_urls = set()
    def parse(self, html: str, current_url: str):
        """PHASE 1: Scan the gallery/directory for Watch Pages"""
        tree = HTMLParser(html)
        links = tree.css('a')
        for link in links:
            href = link.attributes.get('href')
            if not href: continue
            absolute_url = urljoin(current_url, href)
            if absolute_url.endswith(('.mp4', '.webm', '.mkv')):
                title = link.text(strip=True) or absolute_url.split('/')[-1]
                yield VideoItem(url=current_url, title=title, image_url=absolute_url)
            elif '/vids/' in absolute_url and absolute_url not in self.visited_urls:
                self.visited_urls.add(absolute_url)
                print(f"[DRILL-DOWN] Entering watch page: {absolute_url}")
                yield Request(url=absolute_url, callback=self.parse_video_page)
                
    def parse_video_page(self, html: str, current_url: str):
        """PHASE 2: Extract the high-res media and metadata from the isolated page"""
        tree = HTMLParser(html)
        video_node = tree.css_first('video source, video')
        title_node = tree.css_first('h1') 
        if video_node:
            src = video_node.attributes.get('src')
            if src:
                absolute_media_url = urljoin(current_url, src)
                title = title_node.text(strip=True) if title_node else current_url.split('/')[-1]
                print(f"[MEDIA LOCKED] Found nested video stream: {title}")
                yield VideoItem(
                    url=current_url,
                    title=title,
                    image_url=absolute_media_url
                )