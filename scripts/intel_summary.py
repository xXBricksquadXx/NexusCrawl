import sqlite3
import argparse
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel
from typing import List

client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    ),
    mode=instructor.Mode.JSON,
)

class CivicBriefing(BaseModel):
    executive_summary: str
    voting_actions: List[str]
    financial_highlights: List[str]
    contracts_and_grants: List[str]

def generate_briefing(target_file=None, output_file="Executive_Audit_Briefing.md"):
    db_path = "parsed_intel.db"
    if not os.path.exists(db_path):
        print(f"[ERROR] {db_path} not found. Run pdf_parser.py first.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if target_file:
        cursor.execute(
            "SELECT source_file, content FROM extracted_text WHERE source_file LIKE ?",
            (f"%{target_file}%",),
        )
    else:
        cursor.execute("SELECT source_file, content FROM extracted_text")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print(f"[RESULT] No data found for target: {target_file}")
        return
    documents = {}
    for file, content in rows:
        if file not in documents:
            documents[file] = []
        documents[file].append(content)
    print(
        f"[ANALYSIS] Generating Executive Briefings for {len(documents)} documents..."
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Executive Audit Briefing\n\n")
        for file, text_blocks in documents.items():
            print(f"\n[SYNTHESIZING] {file}...")
            full_text = "\n".join(text_blocks)
            safe_text = full_text[:20000]
            try:
                intel = client.chat.completions.create(
                    model="llama3.1",
                    response_model=CivicBriefing,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a forensic civic auditor. Synthesize this raw document into a high-level executive briefing. Focus on overarching roll call votes, financial allocations, budget shortfalls, and contracts. Do not hallucinate.",
                        },
                        {"role": "user", "content": safe_text},
                    ],
                )
                f.write(f"## 📄 Document: {file}\n\n")
                f.write(f"**Executive Summary:**\n{intel.executive_summary}\n\n")
                if intel.voting_actions:
                    f.write("**Key Votes & Motions:**\n")
                    for item in intel.voting_actions:
                        f.write(f"- {item}\n")
                    f.write("\n")
                if intel.financial_highlights:
                    f.write("**Financial & Budget Highlights:**\n")
                    for item in intel.financial_highlights:
                        f.write(f"- {item}\n")
                    f.write("\n")
                if intel.contracts_and_grants:
                    f.write("**Contracts & Grants:**\n")
                    for item in intel.contracts_and_grants:
                        f.write(f"- {item}\n")
                    f.write("\n")
                f.write("---\n\n")
            except Exception as e:
                print(f"[ERROR] LLM Failed to synthesize {file}: {e}")
    print(f"\n[SUCCESS] Executive Briefing saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NexusCrawl: Automated Civic Synthesis"
    )
    parser.add_argument(
        "--file", type=str, help="Optional: Target a specific document to summarize."
    )
    args = parser.parse_args()
    generate_briefing(target_file=args.file)