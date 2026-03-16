from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import VideoItem, StreamItem


class MediaArchiveSpider(BaseSpider):
    name = "media_archive"
    start_urls = []
    drill_down_patterns = [
        "/watch",
        "/video",
        "/livestream",
        "/vids/",
        "youtube.com/watch",
    ]

    def __init__(self):
        self.visited_urls = set()

    def parse(self, html: str, current_url: str):
        if current_url not in self.visited_urls and any(
            p in current_url.lower() for p in self.drill_down_patterns
        ):
            self.visited_urls.add(current_url)
            print(f"[DIRECT STRIKE] Routing root URL to yt-dlp: {current_url}")
            yield StreamItem(
                title=current_url.split("/")[-1].split("?")[0] or "Direct_Video",
                stream_url=current_url,
            )
        tree = HTMLParser(html)
        links = tree.css("a")
        for link in links:
            href = link.attributes.get("href")
            if not href:
                continue
            absolute_url = urljoin(current_url, href)
            if absolute_url.endswith((".mp4", ".webm", ".mkv")):
                title = link.text(strip=True) or absolute_url.split("/")[-1]
                yield VideoItem(url=current_url, title=title, image_url=absolute_url)
            elif any(
                pattern in absolute_url.lower() for pattern in self.drill_down_patterns
            ):
                if absolute_url not in self.visited_urls:
                    self.visited_urls.add(absolute_url)
                    title = link.text(strip=True) or absolute_url.split("/")[-1]
                    print(f"[DRILL-DOWN] Routing watch page to yt-dlp: {absolute_url}")
                    yield StreamItem(title=title, stream_url=absolute_url)
