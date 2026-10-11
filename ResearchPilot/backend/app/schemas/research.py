from pydantic import BaseModel
from typing import List, Optional, Any

class UploadedFileMeta(BaseModel):
    filename: str
    size: Optional[int] = 0
    path: Optional[str] = ""
    extracted_text_path: Optional[str] = None

class ResearchSubmitResponse(BaseModel):
    status: str
    research_question: str
    sources: Optional[List[str]] = []
    uploaded_files: List[UploadedFileMeta]

class SupervisorRequest(BaseModel):
    research_question: str
    goals: Optional[str] = None
    constraints: Optional[str] = None
    sources: Optional[List[str]] = []
    uploaded_files: List[UploadedFileMeta] = []
