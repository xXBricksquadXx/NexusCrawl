import sqlite3
import csv
import os

def export_table_to_csv(db_name: str, table_name: str, output_filename: str):
    if not os.path.exists(db_name):
        print(f"[ERROR] Database {db_name} not found.")
        return

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Pull all data from the target table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"[WARNING] Table '{table_name}' is empty or does not exist.")
            return
            
        # Get column headers dynamically
        column_names = [description[0] for description in cursor.description]
        
        # Write to CSV
        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(column_names)
            writer.writerows(rows)
            
        print(f"[SUCCESS] Exported {len(rows)} records to {output_filename}")
        
    except sqlite3.OperationalError as e:
        print(f"[ERROR] SQLite Error on {table_name}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n[EXPORTER] Initializing Data Dump...\n")
    
    # 1. Export the structured financials (Main DB)
    export_table_to_csv("nexus_database.db", "budget_items", "financial_audit_export.csv")
    
    # 2. Export the mass raw text (Intel DB)
    export_table_to_csv("parsed_intel.db", "extracted_text", "raw_text_export.csv")
    
    print("\n[EXPORTER] Operation Complete. Check root directory for .csv files.")