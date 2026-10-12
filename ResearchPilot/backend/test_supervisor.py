from app.schemas.research import SupervisorRequest
from app.agents.supervisor_agent import supervisor_agent
import traceback

request = SupervisorRequest(
    research_question="Discovery of selective small-molecule allosteric inhibitors for KRAS G12D in pancreatic cancer",
    goals="Identify novel bioactive chemical scaffolds with high binding affinity (Kd < 50 nM) and favorable ADMET characteristics",
    constraints="Focus on molecules obeying Lipinski's Rule of Five, minimizing wild-type KRAS toxicity, and validated in mammalian cancer models",
    uploaded_files=[]
)

try:
    response = supervisor_agent.process(request)
    print("SUCCESS!")
    print(response.model_dump_json(indent=2))
except Exception as e:
    print("FAILED!")
    traceback.print_exc()
