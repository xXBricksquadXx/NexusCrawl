import json
import aiofiles
import os
import httpx
from pydantic import BaseModel

class JsonLinesPipeline:
    def __init__(self, filepath: str = "archive.jsonl"):
        self.filepath = filepath
    async def process_item(self, item: BaseModel):
        """
        Takes a validated Pydantic item, serializes it, and async-appends 
        it to our archive file without blocking the engine's event loop.
        """
        item_dict = item.model_dump(mode='json')
        line = json.dumps(item_dict) + "\n"
        async with aiofiles.open(self.filepath, mode='a', encoding='utf-8') as f:
            await f.write(line)
        print(f"[PIPELINE] Archived to disk: {item_dict.get('title', 'Unknown Item')}")
class AsyncMediaPipeline:
    def __init__(self, media_dir: str = "media"):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True) 
    async def download_image(self, media_url: str, filename: str):
        if not media_url: return
        import os
        from urllib.parse import urlparse
        ext = os.path.splitext(urlparse(media_url).path)[1] or ".bin"
        safe_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ' -_']).rstrip() + ext
        filepath = os.path.join(self.media_dir, safe_filename)
        if os.path.exists(filepath): return 
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client: 
            try:
                async with client.stream('GET', media_url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            await f.write(chunk)
                print(f"[MEDIA] Archived: {safe_filename}")
            except Exception as e:
                print(f"[MEDIA ERROR] Failed on {media_url}: {e}")