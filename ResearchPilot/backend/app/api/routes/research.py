from fastapi import APIRouter, UploadFile, File, Form
from typing import List, Optional
from app.schemas.research import ResearchSubmitResponse
from app.services.file_service import save_upload_files

router = APIRouter()

import json

@router.post("/submit", response_model=ResearchSubmitResponse)
async def submit_research(
    research_question: str = Form(...),
    goals: Optional[str] = Form(None),
    constraints: Optional[str] = Form(None),
    sources: Optional[str] = Form(None),
    files: List[UploadFile] = File([])
):
    # Save the files and get metadata
    uploaded_files_meta = save_upload_files(files)

    parsed_sources = []
    if sources:
        try:
            parsed = json.loads(sources)
            if isinstance(parsed, list):
                parsed_sources = [str(s).strip().lower() for s in parsed if str(s).strip()]
        except Exception:
            parsed_sources = [s.strip().lower() for s in sources.split(",") if s.strip()]

    return ResearchSubmitResponse(
        status="received",
        research_question=research_question,
        sources=parsed_sources,
        uploaded_files=uploaded_files_meta
    )
