from app.schemas.supervisor import SupervisorResponse
from app.schemas.research import SupervisorRequest
from app.services.local_llm_service import local_llm_service
import json

class SupervisorAgent:
    def __init__(self):
        self.prompt_template = """You are the Supervisor Agent of ResearchPilot.

Your responsibilities:
Generate one task for each of these agents in order:
1. Literature Search Agent – Search and retrieve relevant scientific literature based on the research question and constraints.
2. Hypothesis Generator Agent – Generate evidence-informed research hypotheses from the retrieved literature.
3. Critic & Evidence Agent – Evaluate each hypothesis for supporting evidence, contradictions, novelty, assumptions, and weaknesses.
4. Refinement & Research Planner Agent – Refine the best hypothesis and prepare a detailed research plan.
5. Research Plan – Compile the objective, hypothesis, methodology, expected results, timeline, and resources.
6. Human Experimentation – Define the experiments, datasets, or validation steps required for researchers.
7. Memory Update & Learning Loop – Specify what findings, hypotheses, and results should be stored for future research cycles.

Return valid JSON only.

Input Parameters:
Research Question: {research_question}
Goals: {goals}
Constraints: {constraints}
Uploaded Files: {uploaded_files}

Expected JSON Output Format (Do not output anything else):
{{
  "workflow_name": "Drug Discovery Research",
  "agent_tasks": [
    {{
      "agent": "Literature Search Agent",
      "task": "Find recent papers on AI-driven Alzheimer's drug discovery from PubMed, Semantic Scholar, and arXiv."
    }},
    {{
      "agent": "Hypothesis Generator Agent",
      "task": "Generate novel hypotheses for AI-assisted identification of Alzheimer's inhibitors."
    }},
    {{
      "agent": "Critic & Evidence Agent",
      "task": "Evaluate each hypothesis for scientific plausibility, supporting evidence, contradictions, and novelty."
    }},
    {{
      "agent": "Refinement & Research Planner Agent",
      "task": "Refine the strongest hypothesis and create a detailed research plan."
    }},
    {{
      "agent": "Research Plan",
      "task": "Compile objectives, methodology, expected outcomes, timeline, and required resources."
    }},
    {{
      "agent": "Human Experimentation",
      "task": "Define molecular docking, validation experiments, and dataset requirements."
    }},
    {{
      "agent": "Memory Update & Learning Loop",
      "task": "Specify which hypotheses, findings, and experimental results should be stored for future iterations."
    }}
  ]
}}"""

    def process(self, request: SupervisorRequest) -> SupervisorResponse:
        file_metadata_str = json.dumps([f.model_dump() for f in request.uploaded_files], indent=2)
        
        prompt = self.prompt_template.format(
            research_question=request.research_question,
            goals=request.goals or "None specified",
            constraints=request.constraints or "None specified",
            uploaded_files=file_metadata_str
        )
        
        response_dict = local_llm_service.generate_json_response(prompt)
        # Parse it into the Pydantic schema
        return SupervisorResponse(**response_dict)

supervisor_agent = SupervisorAgent()
