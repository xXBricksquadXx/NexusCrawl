import sqlite3
import argparse
import re


def search_intel(keywords: list):
    conn = sqlite3.connect("parsed_intel.db")
    cursor = conn.cursor()
    keyword_display = "', '".join(keywords)
    print(f"\n[INTELLIGENCE SWEEP] Hunting for targets: '{keyword_display}'...\n")
    where_clauses = ["content LIKE ?" for _ in keywords]
    query = f"""
        SELECT source_file, page_number, content 
        FROM extracted_text 
        WHERE {' OR '.join(where_clauses)}
    """
    params = [f"%{kw}%" for kw in keywords]
    cursor.execute(query, params)
    results = cursor.fetchall()
    if not results:
        print(f"[RESULT] No occurrences found in the vault.")
        conn.close()
        return
    print(f"[RESULT] Found {len(results)} page matches.\n")
    print("=" * 70)
    escaped_kws = [re.escape(kw) for kw in sorted(keywords, key=len, reverse=True)]
    pattern = re.compile(f"({'|'.join(escaped_kws)})", re.IGNORECASE)
    for file, page, content in results:
        matches = [m.span() for m in pattern.finditer(content)]
        print(f"📄 FILE: {file} | PAGE: {page}")
        for start, end in matches[:3]:
            window_start = max(0, start - 80)
            window_end = min(len(content), end + 80)
            snippet = content[window_start:window_end].replace("\n", " ")
            snippet = pattern.sub(r" [ \1 ] ", snippet)
            prefix = "..." if window_start > 0 else ""
            suffix = "..." if window_end < len(content) else ""
            print(f"   -> {prefix}{snippet}{suffix}")
        print("-" * 70)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NexusCrawl: Multi-Vector Intelligence Search"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        required=True,
        help="One or more target words or phrases to hunt for.",
    )
    args = parser.parse_args()
    search_intel(args.keywords)
