from selectolax.parser import HTMLParser
from spiders.base import BaseSpider
from models import TableRowItem
class TableDataSpider(BaseSpider):
    name = "table_miner"
    start_urls = ["https://www.w3schools.com/html/html_tables.asp"] 
    def parse(self, html: str, current_url: str):
        tree = HTMLParser(html)
        tables = tree.css('table')
        for table in tables:
            table_id = table.attributes.get('id', 'unknown_table')
            headers = [th.text(strip=True) for th in table.css('th')]
            rows = table.css('tbody tr')
            for row in rows:
                cells = [td.text(strip=True) for td in row.css('td')]
                if len(headers) == len(cells):
                    row_dict = dict(zip(headers, cells))
                    yield TableRowItem(
                        url=current_url,
                        table_id=table_id,
                        row_data=row_dict
                    )