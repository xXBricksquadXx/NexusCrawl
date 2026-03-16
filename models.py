from pydantic import BaseModel, HttpUrl
from dataclasses import dataclass
from typing import Callable, Optional

# --- ENGINE ROUTING ---
@dataclass
class Request:
    url: str
    callback: Callable
    render_js: bool = False
    
# --- EXTRACTION SCHEMAS ---
class CivicItem(BaseModel):
    url: str
    title: str
    dataset_id: Optional[str] = None
    image_url: Optional[str] = None

class VideoItem(BaseModel):
    url: str
    title: str
    image_url: Optional[str] = None # Triggers media pipeline

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