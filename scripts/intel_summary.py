import sqlite3
import argparse
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=600.0,
        max_retries=0,
    ),
    mode=instructor.Mode.JSON,
)


class CivicBriefing(BaseModel):
    executive_summary: str = Field(
        description="A 2-3 paragraph high-level summary of the meeting."
    )
    voting_actions: List[str] = Field(
        default=[],
        description="An array of simple text strings. Each string is one bullet point summarizing a key vote.",
    )
    financial_highlights: List[str] = Field(
        default=[],
        description="An array of simple text strings highlighting budget items.",
    )
    contracts_and_grants: List[str] = Field(
        default=[],
        description="An array of simple text strings highlighting contracts.",
    )


def generate_briefing(target_file=None, output_file="Executive_Audit_Briefing.md"):
    db_path = "nexus_database.db"
    if not os.path.exists(db_path):
        print(f"[ERROR] {db_path} not found. Run nlp_nuke.py first.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = (
        "SELECT source_file, date, motion_by, seconded_by, outcome FROM meeting_votes"
    )
    params = []
    if target_file:
        query += " WHERE source_file LIKE ?"
        params.append(f"%{target_file}%")
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print(f"[RESULT] No structured vote data found for target.")
        return
    documents = {}
    for file_ref, subject, motion, second, outcome in rows:
        base_file = file_ref.split(" (Pg ")[0] if " (Pg " in file_ref else file_ref
        if base_file not in documents:
            documents[base_file] = []
        record = f"Subject: {subject} | Motion: {motion} | Second: {second} | Result: {outcome}"
        documents[base_file].append(record)
    print(
        f"[ANALYSIS] Generating Executive Briefings for {len(documents)} documents..."
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Executive Audit Briefing\n\n")
        for file, records in documents.items():
            print(f"\n[SYNTHESIZING] {file}...")
            structured_text = "\n".join(records)
            try:
                intel = client.chat.completions.create(
                    model="llama3.2",
                    response_model=CivicBriefing,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a forensic civic auditor. Synthesize this structured voting ledger into a high-level executive briefing. "
                                "CRITICAL INSTRUCTION: You MUST output flat arrays of strings for the bullet point sections. "
                                "ABSOLUTELY NO NESTED DICTIONARIES. "
                                'Example of VALID format: {"voting_actions": ["Approved $5k for roads (Carried, 15-0)", "Tabled the wheel tax (Failed)"]} '
                                'Example of INVALID format: {"voting_actions": [{"motion": "roads", "result": "carried"}]} -> THIS WILL CRASH THE SYSTEM.'
                            ),
                        },
                        {"role": "user", "content": structured_text},
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
