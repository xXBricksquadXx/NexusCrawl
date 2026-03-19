import sqlite3
import time
import argparse
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional, Union

client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=300.0,
        max_retries=0,
    ),
    mode=instructor.Mode.JSON,
)


class RollCallVote(BaseModel):
    resolution_id: Optional[Union[str, int]] = Field(
        default=None, description="Resolution ID or item number. Return null if none."
    )
    subject: Optional[str] = Field(
        default="Unknown Subject", description="Summary of the vote."
    )
    motion_by: Optional[str] = Field(
        default="Unknown",
        description="Exact name of the person who made the motion. Do NOT carry over names.",
    )
    seconded_by: Optional[str] = Field(
        default="Unknown", description="Exact name of the person who seconded."
    )
    ayes: Optional[List[str]] = Field(
        default=[], description="List of names voting Aye."
    )
    nays: Optional[List[str]] = Field(
        default=[], description="List of names voting No."
    )
    abstains: Optional[List[str]] = Field(
        default=[], description="List of names who abstained."
    )
    absent: Optional[List[str]] = Field(default=[], description="List of absent names.")
    outcome: Optional[str] = Field(
        default="Unknown", description="The final result (e.g., 'CARRIED', 'FAILED')."
    )


class PageIntelligence(BaseModel):
    votes: List[RollCallVote] = Field(
        default=[],
        description="Extract distinct votes. Return empty array if no motions exist.",
    )


def detonate_nuke(target_file=None, target_page=None):
    conn = sqlite3.connect("parsed_intel.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "ALTER TABLE extracted_text ADD COLUMN ai_processed INTEGER DEFAULT 0"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass
    query = """
        SELECT id, source_file, page_number, content 
        FROM extracted_text 
        WHERE (content LIKE '%Upon motion%' 
           OR content LIKE '%seconded by%' 
           OR content LIKE '%roll call vote%')
    """
    params = []
    if target_file:
        query += " AND source_file = ?"
        params.append(target_file)
    if target_page:
        query += " AND page_number = ?"
        params.append(target_page)
    if not target_file and not target_page:
        query += " AND (ai_processed = 0 OR ai_processed IS NULL)"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if not rows:
        print("[NUKE] No targets found or all pages already processed. Exiting.")
        return
    print(
        f"[NUKE] Refined Targets acquired: {len(rows)} pages. Commencing precision strike...\n"
    )
    vault_conn = sqlite3.connect("nexus_database.db")
    vault_cursor = vault_conn.cursor()
    for row_id, file, page, content in rows:
        print(f"[STRIKE] Analyzing {file} (Page {page})...")
        safe_content = content[:4000]
        start_time = time.time()
        try:
            intel = client.chat.completions.create(
                model="llama3.2",
                response_model=PageIntelligence,
                max_tokens=2000,
                max_retries=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a forensic parliamentary auditor. Isolate voting events. "
                            "KILL LIST: Completely ignore Invocations, Pledges of Allegiance, Prayers, Public Comments, and Announcements. "
                            "FORMATTING: List names as simple strings. Do NOT use nested objects. "
                            "VOICE VOTES: If the text says 'voice vote' or 'All present voted Aye', DO NOT guess names. Leave the ayes, nays, abstains, and absent arrays COMPLETELY EMPTY. Set outcome to 'VOICE VOTE - CARRIED'. "
                            "IMPORTANT: Return a JSON object with exactly ONE root key called 'votes'. Do NOT wrap the output in a 'pageIntelligence' key."
                        ),
                    },
                    {"role": "user", "content": safe_content},
                ],
            )
            if not intel.votes:
                print(
                    "  -> [CLEAR] No distinct votes found on this page. (Noise bypassed)"
                )
            for vote in intel.votes:
                safe_res_id = (
                    str(vote.resolution_id)
                    if vote.resolution_id is not None
                    else "None"
                )
                safe_subject = vote.subject or "Unknown Subject"
                safe_outcome = (vote.outcome or "Unknown").upper()
                safe_motion = vote.motion_by or "Unknown"
                safe_second = vote.seconded_by or "Unknown"
                safe_ayes = vote.ayes or []
                safe_nays = vote.nays or []
                safe_abstains = vote.abstains or []
                safe_absent = vote.absent or []
                print(f"  -> Resolution: {safe_res_id} | Subject: {safe_subject}")
                print(f"  -> Motion: {safe_motion} | Second: {safe_second}")
                print(
                    f"  -> Ayes ({len(safe_ayes)}) | Nays ({len(safe_nays)}) | Abstains ({len(safe_abstains)}) | Absent ({len(safe_absent)})"
                )
                print(f"  -> Outcome: {safe_outcome}")
                vault_cursor.execute(
                    """
                    INSERT INTO meeting_votes 
                    (source_file, date, motion_by, seconded_by, outcome) 
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        f"{file} (Pg {page})",
                        safe_subject,
                        safe_motion,
                        safe_second,
                        f"{safe_outcome} | Ayes: {len(safe_ayes)} | Nays: {len(safe_nays)} | Abstains: {len(safe_abstains)} | Absent: {len(safe_absent)}",
                    ),
                )
                print("  -> [VAULTED TO SQLITE]")
                print("-" * 50)
            vault_conn.commit()
            cursor.execute(
                "UPDATE extracted_text SET ai_processed = 1 WHERE id = ?", (row_id,)
            )
            conn.commit()
        except Exception as e:
            print(f"[ERROR] Extraction failed on Row {row_id}: {e}")
        elapsed_time = time.time() - start_time
        print(f"[TELEMETRY] Page cleared in {elapsed_time:.2f} seconds.\n")
    conn.close()
    vault_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NexusCrawl: NLP Nuke - Parliamentary Extraction"
    )
    parser.add_argument("--file", type=str, help="Target a specific PDF file")
    parser.add_argument("--page", type=int, help="Target a specific page number")
    args = parser.parse_args()
    detonate_nuke(target_file=args.file, target_page=args.page)
