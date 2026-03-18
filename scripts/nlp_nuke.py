import sqlite3
import time
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=900.0,
        max_retries=0,
    ),
    mode=instructor.Mode.JSON,
)

class RollCallVote(BaseModel):
    resolution_id: Optional[str] = Field(
        description="The ID of the resolution (e.g., '2024-22'). Return null if none."
    )
    subject: str = Field(description="A concise summary of what is being voted on.")
    motion_by: Optional[str] = Field(
        description="The exact name of the person who made the motion for THIS specific vote. Do not carry over names from previous votes."
    )
    seconded_by: Optional[str] = Field(
        description="The exact name of the person who seconded THIS specific vote."
    )
    ayes: List[str] = Field(description="List of names voting Aye.")
    nays: List[str] = Field(
        description="List of names voting No. If the text says 'No: None', this array MUST be absolutely empty."
    )
    abstains: List[str] = Field(default=[], description="List of names who abstained.")
    absent: List[str] = Field(default=[], description="List of absent names.")
    outcome: str = Field(
        description="The final result (e.g., 'CARRIED', 'FAILED', 'APPROVED')."
    )

class PageIntelligence(BaseModel):
    votes: List[RollCallVote] = Field(
        description="Extract every single distinct vote on the page. Treat each vote as a completely isolated event."
    )
    key_takeaway: str = Field(description="A 1-sentence summary of the page.")

def detonate_nuke():
    conn = sqlite3.connect("parsed_intel.db")
    cursor = conn.cursor()
    # Safeties Off: LIMIT 3 removed for full execution
    cursor.execute("""
        SELECT id, source_file, page_number, content 
        FROM extracted_text 
        WHERE content LIKE '%Upon motion of%' OR content LIKE '%RESOLUTION%'
    """)
    rows = cursor.fetchall()
    print(
        f"[NUKE] Targets acquired: {len(rows)} pages. Commencing precision strike...\n"
    )
    vault_conn = sqlite3.connect("nexus_database.db")
    vault_cursor = vault_conn.cursor()
    for row_id, file, page, content in rows:
        print(f"[STRIKE] Analyzing {file} (Page {page})...")
        start_time = time.time()
        try:
            intel = client.chat.completions.create(
                model="llama3.1",
                response_model=PageIntelligence,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a forensic parliamentary auditor. Read the OCR text carefully. Isolate every single voting event. Do NOT mix up the people who made the motion with previous motions. If 'No: None' is written, the nays array must be empty. If a page has no motions or resolutions, return an empty votes array.",
                    },
                    {"role": "user", "content": content},
                ],
            )
            if not intel.votes:
                print("  -> [CLEAR] No distinct votes found on this page.")
            for vote in intel.votes:
                print(
                    f"  -> Resolution: {vote.resolution_id} | Subject: {vote.subject}"
                )
                print(f"  -> Motion: {vote.motion_by} | Second: {vote.seconded_by}")
                print(
                    f"  -> Ayes ({len(vote.ayes)}) | Nays ({len(vote.nays)}) | Abstains ({len(vote.abstains)})"
                )
                print(f"  -> Outcome: {vote.outcome.upper()}")
                vault_cursor.execute(
                    """
                    INSERT INTO meeting_votes 
                    (source_file, date, motion_by, seconded_by, outcome) 
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        f"{file} (Pg {page})",
                        vote.subject,
                        vote.motion_by or "Unknown",
                        vote.seconded_by or "Unknown",
                        f"{vote.outcome.upper()} | Ayes: {len(vote.ayes)} | Nays: {len(vote.nays)} | Abstains: {len(vote.abstains)}",
                    ),
                )
                print("  -> [VAULTED TO SQLITE]")
                print("-" * 50)
            vault_conn.commit()
        except Exception as e:
            print(f"[ERROR] Extraction failed on Row {row_id}: {e}")
        elapsed_time = time.time() - start_time
        print(f"[TELEMETRY] Page cleared in {elapsed_time:.2f} seconds.\n")
    conn.close()
    vault_conn.close()

if __name__ == "__main__":
    detonate_nuke()