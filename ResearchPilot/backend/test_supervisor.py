from app.schemas.research import SupervisorRequest
from app.agents.supervisor_agent import supervisor_agent
import traceback

request = SupervisorRequest(
    research_question="How to optimize serverless cold starts?",
    goals="Test",
    constraints="None",
    uploaded_files=[]
)

try:
    response = supervisor_agent.process(request)
    print("SUCCESS!")
    print(response.model_dump_json(indent=2))
except Exception as e:
    print("FAILED!")
    traceback.print_exc()
