from pydantic import BaseModel
from typing import List, Optional
from app.schemas.research import UploadedFileMeta

class LiteratureRequest(BaseModel):
    research_question: str
    uploaded_files: List[UploadedFileMeta] = []
    max_web_results: Optional[int] = 4

class PaperSummary(BaseModel):
    filename: str
    title: Optional[str] = None
    source_type: str = "uploaded"  # "uploaded" or "web_discovered"
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    authors: Optional[List[str]] = []
    year: Optional[int] = None
    summary: str
    important_points: List[str] = []

class LiteratureResponse(BaseModel):
    summaries: List[PaperSummary] = []
    uploaded_summaries: List[PaperSummary] = []
    discovered_papers: List[PaperSummary] = []
    synthesis: Optional[str] = ""
