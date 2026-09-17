from pydantic import BaseModel
from typing import List

class AgentTask(BaseModel):
    agent: str
    task: str

class SupervisorResponse(BaseModel):
    workflow_name: str
    agent_tasks: List[AgentTask]
