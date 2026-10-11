from pydantic import BaseModel
from typing import List, Optional
from app.schemas.research import UploadedFileMeta

class LiteratureRequest(BaseModel):
    research_question: str
    uploaded_files: List[UploadedFileMeta] = []

class PaperSummary(BaseModel):
    filename: str
    summary: str
    important_points: List[str]

class LiteratureResponse(BaseModel):
    summaries: List[PaperSummary]
