import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import asyncio
import argparse
import re
import pdfplumber
from models import ParsedTable, ParsedText, BudgetLineItem
from core.pipeline import ParsedIntelPipeline, SQLitePipeline


class PDFExploiter:
    def __init__(self, media_dir="media"):
        self.media_dir = media_dir
        self.intel_pipeline = ParsedIntelPipeline()
        self.sql_pipeline = SQLitePipeline()

    def _sanitize_string(self, text: str) -> str:
        """Removes stray watermark letters (like 'R', 'D', 'F') and cleans whitespace."""
        if not text:
            return ""
        cleaned = re.sub(r"\b[A-Z]\b", "", text)
        return cleaned.strip()

    async def analyze_file(self, filename: str):
        filepath = os.path.join(self.media_dir, filename)
        if not os.path.exists(filepath):
            print(f"[ERROR] File not found: {filepath}")
            return
        print(f"\n[ANALYZING] {filename}")
        try:
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        await self.intel_pipeline.process_item(
                            ParsedText(
                                source_file=filename,
                                page_number=page_num,
                                content=text.strip(),
                            )
                        )
                    custom_settings = {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "intersection_x_tolerance": 15,
                    }
                    tables = page.extract_tables(table_settings=custom_settings)
                    for t_idx, table in enumerate(tables, start=1):
                        if not table or len(table) < 2:
                            continue
                        for row in table:
                            raw_cells = [
                                str(cell).replace("\n", " ").strip() if cell else ""
                                for cell in row
                            ]
                            data_cells = [cell for cell in raw_cells if cell != ""]
                            if len(data_cells) < 2:
                                continue
                            primary_cell = self._sanitize_string(data_cells[0])
                            match = re.match(r"^(\d{5})\s+(.+)", primary_cell)
                            if match:
                                account_code = match.group(1)
                                description = match.group(2).strip()
                                amount_str = data_cells[-1].strip()
                                if not any(char.isdigit() for char in amount_str):
                                    continue
                                await self.sql_pipeline.process_item(
                                    BudgetLineItem(
                                        source_file=filename,
                                        department="General Fund",
                                        account_code=account_code,
                                        description=description,
                                        amount=amount_str,
                                    )
                                )
                                print(
                                    f"  -> Extracted Budget Item: [{account_code}] {description[:25]}... -> {amount_str}"
                                )
        except Exception as e:
            print(f"[ERROR] Failed processing {filename}: {e}")

    async def run_mass_exploitation(self):
        print(f"[EXPLOITER] Scanning {self.media_dir} for PDF assets...")
        for filename in os.listdir(self.media_dir):
            if filename.endswith(".pdf"):
                await self.analyze_file(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusCrawl: PDF Intelligence Parser")
    parser.add_argument(
        "--file", type=str, help="Parse a specific PDF file in the media directory."
    )
    args = parser.parse_args()
    exploiter = PDFExploiter()
    if args.file:
        asyncio.run(exploiter.analyze_file(args.file))
    else:
        asyncio.run(exploiter.run_mass_exploitation())
