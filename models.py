from pydantic import BaseModel, HttpUrl
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class Request:
    url: str
    callback: Callable
    render_js: bool = False

class CivicItem(BaseModel):
    url: str
    title: str
    dataset_id: Optional[str] = None
    image_url: Optional[str] = None

class VideoItem(BaseModel):
    url: str
    title: str
    image_url: Optional[str] = None

class TableRowItem(BaseModel):
    url: str
    table_id: str
    row_data: dict

class SourceCodeItem(BaseModel):
    url: str
    file_name: str
    content: str
    sub_dir: str

class StreamItem(BaseModel):
    title: str
    stream_url: str

class ParsedTable(BaseModel):
    source_file: str
    page_number: int
    table_index: int
    row_data: str

class ParsedText(BaseModel):
    source_file: str
    page_number: int
    content: str

# --- INTEL PARSER MODELS ---
class BudgetLineItem(BaseModel):
    source_file: str
    department: Optional[str] = None
    account_code: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None

class MeetingVote(BaseModel):
    source_file: str
    date: Optional[str] = None
    motion_by: Optional[str] = None
    seconded_by: Optional[str] = None
    outcome: Optional[str] = None