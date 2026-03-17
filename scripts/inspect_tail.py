import sqlite3


def inspect_tail():
    conn = sqlite3.connect("nexus_database.db")
    cursor = conn.cursor()
    print("\n--- TAIL 30: STRUCTURED BUDGET ITEMS ---")
    try:
        cursor.execute("""
            SELECT id, account_code, description, amount 
            FROM budget_items 
            ORDER BY id DESC 
            LIMIT 30
        """)
        rows = cursor.fetchall()
        for row in reversed(rows):
            print(
                f"ID: {row[0]:<4} | Code: {row[1]:<6} | Desc: {row[2]:<35} | Amt: {row[3]}"
            )
    except Exception as e:
        print(f"[ERROR] Failed to query database: {e}")
    conn.close()


if __name__ == "__main__":
    inspect_tail()
