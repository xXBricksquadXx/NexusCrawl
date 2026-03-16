import random
import asyncio
import httpx
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
class RetryMiddleware:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.retryable_statuses = [403, 408, 429, 500, 502, 503, 504]
    async def execute_with_retry(self, request, client: httpx.AsyncClient, headers: dict):
        """Wraps the HTTP request in a resilient exponential backoff loop."""
        attempts = 0
        while attempts <= self.max_retries:
            try:
                response = await client.get(request.url, headers=headers)
                if response.status_code not in self.retryable_statuses:
                    response.raise_for_status()
                    return response
                attempts += 1
                backoff_time = 2 ** attempts 
                print(f"[RETRY] Server returned {response.status_code} for {request.url}. Retrying in {backoff_time}s... ({attempts}/{self.max_retries})")
                await asyncio.sleep(backoff_time)
            except httpx.RequestError as e:
                attempts += 1
                backoff_time = 2 ** attempts
                print(f"[NETWORK ERROR] Failed to connect to {request.url}: {e}. Retrying in {backoff_time}s...")
                await asyncio.sleep(backoff_time)
        raise Exception(f"Max retries ({self.max_retries}) exceeded for {request.url}")