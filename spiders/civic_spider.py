from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import Request, CivicItem
class CivicAuditSpider(BaseSpider):
    name = "book_archive"
    start_urls = ["https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"]
    def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        books = tree.css('article.product_pod')
        for book in books:
            title_node = book.css_first('h3 a')
            price_node = book.css_first('p.price_color')
            img_node = book.css_first('div.image_container img') 
            if title_node and price_node:
                img_url = urljoin(current_url, img_node.attributes.get('src')) if img_node else None
                yield CivicItem(
                    url=current_url,
                    title=title_node.attributes.get('title', 'Unknown'),
                    dataset_id=price_node.text(),
                    image_url=img_url 
                )
        next_button = tree.css_first('li.next a')
        if next_button:
            next_href = next_button.attributes.get('href')
            if next_href:
                next_url = urljoin(current_url, next_href)
                print(f"[SPIDER] Discovered new link: {next_url}")
                yield Request(url=next_url, callback=self.parse)