from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import VideoItem
class MediaArchiveSpider(BaseSpider):
    name = "media_archive"
    start_urls = ["https://test-videos.co.uk/"] 
    def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        links = tree.css('a')
        for idx, link in enumerate(links):
            href = link.attributes.get('href', '')
            if href.endswith(('.mp4', '.webm', '.mkv', '.flv')):
                absolute_url = urljoin(current_url, href)
                title = link.text(strip=True) or f"Video_Archive_{idx}"
                yield VideoItem(
                    url=current_url,
                    title=title,
                    image_url=absolute_url 
                )