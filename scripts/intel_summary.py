import sqlite3
import argparse
import re
import os
import csv

DEFAULT_THREATS = [
    "fraud",
    "misappropriation",
    "shortage",
    "indicted",
    "unauthorized",
    "deficit",
    "embezzlement",
    "subpoena",
    "noncompliance",
    "unallowable",
    "malfeasance",
]


def generate_matrix(target_location=None, output_format="md", context_size=400):
    db_path = "parsed_intel.db"
    if not os.path.exists(db_path):
        print(f"[ERROR] {db_path} not found. Run the pdf_parser first.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if target_location:
        print(f"\n[SWEEP] Isolating files mentioning: '{target_location}'...")
        cursor.execute(
            "SELECT source_file, page_number, content FROM extracted_text WHERE content LIKE ?",
            (f"%{target_location}%",),
        )
    else:
        print("\n[SWEEP] Executing global sweep across ALL files...")
        cursor.execute("SELECT source_file, page_number, content FROM extracted_text")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print(f"[RESULT] No data found for target: {target_location}")
        return
    print(f"[ANALYSIS] Scanning {len(rows)} pages for threat indicators...")
    findings = []
    threat_pattern = re.compile(
        r"\b(" + "|".join(DEFAULT_THREATS) + r")\b", re.IGNORECASE
    )
    for file, page, content in rows:
        for match in threat_pattern.finditer(content):
            threat_word = match.group(1).lower()
            start = match.start()
            end = match.end()
            window_start = max(0, start - (context_size // 2))
            window_end = min(len(content), end + (context_size // 2))
            snippet = content[window_start:window_end].replace("\n", " ")
            findings.append(
                {
                    "file": file,
                    "page": page,
                    "threat": threat_word.upper(),
                    "context": f"...{snippet.strip()}...",
                }
            )
    if not findings:
        print("[CLEAR] No threat indicators found in the dataset.")
        return
    print(f"[ALERT] Found {len(findings)} threat indicators. Generating report...")
    if output_format == "csv":
        output_file = "Threat_Matrix_Report.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "page", "threat", "context"])
            writer.writeheader()
            writer.writerows(findings)
    else:
        output_file = "Threat_Matrix_Report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Executive Audit Briefing\n")
            if target_location:
                f.write(f"**Target Location:** {target_location}\n")
            f.write(f"**Total Anomalies Detected:** {len(findings)}\n\n---\n\n")
            for item in findings:
                f.write(f"### 🚨 {item['threat']}\n")
                f.write(f"- **Source File:** `{item['file']}` (Page {item['page']})\n")
                f.write(f"- **Context:** {item['context']}\n\n")
    print(f"[SUCCESS] Executive Briefing saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusCrawl: Automated Threat Matrix")
    parser.add_argument(
        "--target",
        type=str,
        help="Optional: Filter by a specific county or city (e.g., 'Giles')",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "csv"],
        default="md",
        help="Output format: 'md' (Markdown) or 'csv'",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=400,
        help="Total characters to extract around the threat (default: 400)",
    )
    args = parser.parse_args()
    generate_matrix(
        target_location=args.target,
        output_format=args.format,
        context_size=args.context,
    )
