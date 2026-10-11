from fastapi import APIRouter
from app.api.routes import research, supervisor, literature

api_router = APIRouter()

api_router.include_router(research.router, prefix="/research", tags=["Research Input"])
api_router.include_router(supervisor.router, prefix="/supervisor", tags=["Supervisor Agent"])
api_router.include_router(literature.router, prefix="/literature", tags=["Literature Agent"])
