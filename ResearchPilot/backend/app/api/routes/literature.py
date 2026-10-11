from fastapi import APIRouter, HTTPException
from app.schemas.literature import LiteratureRequest, LiteratureResponse
from app.agents.literature_agent import literature_agent
from app.core.logging import logger

router = APIRouter()

@router.post("/summarize", response_model=LiteratureResponse)
def summarize_literature(request: LiteratureRequest):
    try:
        response = literature_agent.process(request)
        return response
    except Exception as e:
        logger.error(f"Error in Literature Agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to summarize literature")
