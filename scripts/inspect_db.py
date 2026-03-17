import sqlite3


def inspect_intel():
    conn = sqlite3.connect("parsed_intel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT page_number, content FROM extracted_text LIMIT 2")
    rows = cursor.fetchall()
    for page_num, content in rows:
        print(f"\n--- PAGE {page_num} START ---")
        print(content[:1000])
        print(f"--- PAGE {page_num} END ---")
    conn.close()


if __name__ == "__main__":
    inspect_intel()
