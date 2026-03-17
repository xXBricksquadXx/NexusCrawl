import sqlite3
import argparse
import re


def search_intel(keyword: str):
    conn = sqlite3.connect("parsed_intel.db")
    cursor = conn.cursor()
    print(f"\n[INTELLIGENCE SWEEP] Hunting for keyword: '{keyword}'...\n")
    cursor.execute(
        """
        SELECT source_file, page_number, content 
        FROM extracted_text 
        WHERE content LIKE ?
    """,
        (f"%{keyword}%",),
    )
    results = cursor.fetchall()
    if not results:
        print(f"[RESULT] No occurrences of '{keyword}' found in the vault.")
        conn.close()
        return
    print(f"[RESULT] Found {len(results)} page matches.\n")
    print("=" * 70)
    for file, page, content in results:
        matches = [
            m.span() for m in re.finditer(re.escape(keyword), content, re.IGNORECASE)
        ]
        print(f"📄 FILE: {file} | PAGE: {page}")
        for start, end in matches[:2]:
            window_start = max(0, start - 60)
            window_end = min(len(content), end + 60)
            snippet = content[window_start:window_end].replace("\n", " ")
            snippet = re.sub(
                f"({re.escape(keyword)})", r" [ \1 ] ", snippet, flags=re.IGNORECASE
            )
            prefix = "..." if window_start > 0 else ""
            suffix = "..." if window_end < len(content) else ""
            print(f"   -> {prefix}{snippet}{suffix}")
        print("-" * 70)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusCrawl: Intelligence Search")
    parser.add_argument(
        "--keyword",
        type=str,
        required=True,
        help="The target word or phrase to hunt for.",
    )
    args = parser.parse_args()
    search_intel(args.keyword)
