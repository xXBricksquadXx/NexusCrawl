import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from spiders.base import BaseSpider
from models import SourceCodeItem


class WebReconSpider(BaseSpider):
    name = "web_recon"
    start_urls = ["https://example.com/"]
    render_js = True

    async def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        yield SourceCodeItem(
            url=current_url, file_name="index.html", content=html, sub_dir="html"
        )
        css_links = [
            node.attributes.get("href") for node in tree.css('link[rel="stylesheet"]')
        ]
        js_links = [node.attributes.get("src") for node in tree.css("script")]
        assets = [urljoin(current_url, link) for link in (css_links + js_links) if link]
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for asset_url in assets:
                try:
                    resp = await client.get(asset_url)
                    if resp.status_code == 200:
                        file_ext = asset_url.split("?")[0].split(".")[-1]
                        if file_ext not in ["css", "js"]:
                            file_ext = "js" if "script" in asset_url else "css"
                        filename = (
                            asset_url.split("/")[-1].split("?")[0]
                            or f"asset.{file_ext}"
                        )
                        yield SourceCodeItem(
                            url=current_url,
                            file_name=filename,
                            content=resp.text,
                            sub_dir=file_ext,
                        )
                except Exception as e:
                    print(f"[RECON ERROR] Failed to fetch asset {asset_url}: {e}")
