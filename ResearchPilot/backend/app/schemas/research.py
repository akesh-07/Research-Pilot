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
    uploaded_files: List[UploadedFileMeta]

class SupervisorRequest(BaseModel):
    research_question: str
    goals: Optional[str] = None
    constraints: Optional[str] = None
    uploaded_files: List[UploadedFileMeta] = []
