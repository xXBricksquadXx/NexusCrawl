import asyncio
import yt_dlp
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
        item_dict = item.model_dump(mode="json")
        line = json.dumps(item_dict) + "\n"
        async with aiofiles.open(self.filepath, mode="a", encoding="utf-8") as f:
            await f.write(line)
        print(f"[PIPELINE] Archived to disk: {item_dict.get('title', 'Unknown Item')}")


class AsyncMediaPipeline:
    def __init__(self, media_dir: str = "media"):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    async def download_image(self, media_url: str, filename: str):
        if not media_url:
            return
        import os
        from urllib.parse import urlparse

        ext = os.path.splitext(urlparse(media_url).path)[1] or ".bin"
        safe_filename = (
            "".join(
                [c for c in filename if c.isalpha() or c.isdigit() or c in " -_"]
            ).rstrip()
            + ext
        )
        filepath = os.path.join(self.media_dir, safe_filename)
        if os.path.exists(filepath):
            return
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                async with client.stream("GET", media_url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(filepath, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            await f.write(chunk)
                print(f"[MEDIA] Archived: {safe_filename}")
            except Exception as e:
                print(f"[MEDIA ERROR] Failed on {media_url}: {e}")


class SourceCodePipeline:
    def __init__(self, base_dir: str = "recon_vault"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def process_item(self, item: BaseModel):
        from urllib.parse import urlparse
        import aiofiles
        import os

        domain = urlparse(item.url).netloc.replace("www.", "")
        target_dir = os.path.join(self.base_dir, domain, item.sub_dir)
        os.makedirs(target_dir, exist_ok=True)
        safe_filename = "".join(
            [c for c in item.file_name if c.isalnum() or c in " .-_"]
        ).rstrip()
        filepath = os.path.join(target_dir, safe_filename)
        async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
            await f.write(item.content)
        print(f"[RECON PIPELINE] Cloned: {item.sub_dir}/{safe_filename}")


class YTDLPPipeline:
    def __init__(self, media_dir: str = "media/streams"):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    def _sync_download(self, url: str):
        """Synchronous yt-dlp execution block"""
        ydl_opts = {
            "outtmpl": f"{self.media_dir}/%(title)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[YT-DLP] Intercepting stream for: {url}")
            ydl.download([url])

    async def process_item(self, item: BaseModel):
        if not getattr(item, "stream_url", None):
            return
        try:
            await asyncio.to_thread(self._sync_download, item.stream_url)
            print(f"[PIPELINE] Stream successfully stitched and archived: {item.title}")
        except Exception as e:
            print(
                f"[YT-DLP ERROR] Failed to extract stream from {item.stream_url}: {e}"
            )
