from selectolax.parser import HTMLParser
from spiders.base import BaseSpider
from models import TableRowItem
class TableDataSpider(BaseSpider):
    name = "table_miner"
    start_urls = ["https://datatables.net/"] 
    render_js = True 
    async def interact_with_page(self, page):
        """This executes inside the Playwright browser BEFORE HTML extraction"""
        print("[SPIDER] Instructing browser to show 100 entries...")
        dropdown = page.locator('select').first
        await dropdown.select_option(value="100")
        await page.wait_for_selector('tbody tr:nth-child(11)', timeout=5000)
        print("[SPIDER] Table expanded.")
    def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        tables = tree.css('table')
        for table in tables:
            table_id = table.attributes.get('id', 'unknown_table')
            header_nodes = table.css('thead th')
            if not header_nodes:
                header_nodes = table.css('tr th')
            headers = [th.text(strip=True) for th in header_nodes]
            rows = table.css('tbody tr')
            for row in rows:
                cells = [td.text(strip=True) for td in row.css('td')]
                if len(headers) == len(cells) and len(cells) > 0: 
                    row_dict = dict(zip(headers, cells))
                    yield TableRowItem(
                        url=current_url,
                        table_id=table_id,
                        row_data=row_dict
                    )