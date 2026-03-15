class BaseSpider:
    name = "base"
    start_urls = []

    def parse(self, html: str, current_url: str):
        """Override this in your custom spiders to yield Items or new Requests"""
        raise NotImplementedError