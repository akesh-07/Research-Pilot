import os
from app.schemas.literature import LiteratureRequest, LiteratureResponse, PaperSummary
from app.services.local_llm_service import local_llm_service
from app.core.logging import logger

class LiteratureAgent:
    def __init__(self):
        self.prompt_template = """You are the Literature Search Agent.
Your task is to analyze the content of a provided research paper, generate a summary, and extract important points, keeping the research question in mind.

Research Question: {research_question}

Paper Content:
{paper_content}

Return valid JSON only in the following format:
{{
  "summary": "A comprehensive summary of the paper in the context of the research question...",
  "important_points": [
    "Key finding 1...",
    "Methodology detail...",
    "Limitation or future work..."
  ]
}}
"""

    def process(self, request: LiteratureRequest) -> LiteratureResponse:
        summaries = []
        for file_meta in request.uploaded_files:
            text_path = file_meta.extracted_text_path
            
            if not text_path or not os.path.exists(text_path):
                logger.warning(f"No extracted text found for {file_meta.filename}")
                summaries.append(PaperSummary(
                    filename=file_meta.filename,
                    summary="No text could be extracted from this file, or it was not uploaded properly.",
                    important_points=["Check file format or contents."]
                ))
                continue
                
            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Truncate content to fit in context window (LM Studio default is often ~4k tokens)
                # 1 token is roughly 4 characters, so 3500 tokens is ~14,000 characters. We'll use 10,000 to be safe.
                max_chars = 10000 
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n...[CONTENT TRUNCATED]..."

                prompt = self.prompt_template.format(
                    research_question=request.research_question,
                    paper_content=content
                )
                
                response_dict = local_llm_service.generate_json_response(prompt)
                
                summary = PaperSummary(
                    filename=file_meta.filename,
                    summary=response_dict.get("summary", "No summary generated."),
                    important_points=response_dict.get("important_points", [])
                )
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to process literature for {file_meta.filename}: {e}")
                summary = PaperSummary(
                    filename=file_meta.filename,
                    summary=f"Failed to process this document. Error: {str(e)}",
                    important_points=["Document could not be analyzed."]
                )
                summaries.append(summary)
                
        return LiteratureResponse(summaries=summaries)

literature_agent = LiteratureAgent()
