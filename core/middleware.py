import random
class UserAgentMiddleware:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NexusCrawl/1.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "ArchivalBot/2.0 (+http://nexus.local)"
        ]
    def process_request(self, request_headers: dict) -> dict:
        request_headers["User-Agent"] = random.choice(self.user_agents)
        return request_headers