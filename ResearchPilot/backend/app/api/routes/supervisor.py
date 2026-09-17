from fastapi import APIRouter, HTTPException
from app.schemas.research import SupervisorRequest
from app.schemas.supervisor import SupervisorResponse
from app.agents.supervisor_agent import supervisor_agent
from app.core.logging import logger

router = APIRouter()

@router.post("/tasks", response_model=SupervisorResponse)
async def generate_tasks(request: SupervisorRequest):
    try:
        response = supervisor_agent.process(request)
        return response
    except Exception as e:
        logger.error(f"Error in Supervisor Agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate tasks")
