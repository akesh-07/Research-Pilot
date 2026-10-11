import os
import re
from typing import List, Dict
from app.schemas.literature import LiteratureRequest, LiteratureResponse, PaperSummary
from app.services.local_llm_service import local_llm_service
from app.services.academic_search_service import academic_search_service
from app.core.logging import logger
from app.core.config import settings

class LiteratureAgent:
    def __init__(self):
        self.uploaded_paper_prompt = """You are the Literature Search Agent.
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

        self.web_paper_prompt = """You are the Literature Search Agent.
Analyze this academic paper found on {source_name} and explain its relevance to the user's research question.

Research Question: {research_question}

Paper Title: {paper_title}
Source: {source_name}
Abstract:
{abstract}

Return valid JSON only in the following format:
{{
  "summary": "A concise summary explaining the paper's core contributions and relevance to the research question...",
  "important_points": [
    "Key technique or methodology...",
    "Notable result or finding...",
    "Scientific relevance..."
  ]
}}
"""

        self.synthesis_prompt = """You are the Literature Search Agent.
Synthesize the key insights from the analyzed literature with respect to the user's research question.

Research Question: {research_question}
Analyzed Papers from Selected Sources ({selected_sources}):
{paper_list}

Return valid JSON only in the following format:
{{
  "synthesis": "A coherent synthesis summarizing the overall research landscape, comparing methodologies identified, and highlighting open opportunities related to the research question."
}}
"""

    def generate_search_query(self, research_question: str) -> str:
        """Derive an effective academic search query from the research question."""
        prompt = f"""You are a research assistant. Extract 3 to 6 essential academic keywords from this research question to search scientific literature databases.
Do not use boolean operators, quotes, or punctuation.

Research Question: {research_question}

Return valid JSON only:
{{
  "keywords": "example keyword string"
}}"""
        try:
            res = local_llm_service.generate_json_response(prompt)
            keywords = res.get("keywords", "").strip()
            if keywords:
                return keywords
        except Exception as e:
            logger.warning(f"Could not extract keywords via LLM, using fallback: {e}")

        # Fallback: simple cleanup of the question
        cleaned = re.sub(r'[\?\!\.\:\;\,\"\']', ' ', research_question)
        words = [w for w in cleaned.split() if len(w) > 2 and w.lower() not in {"what", "how", "why", "when", "where", "which", "the", "and", "for", "with", "from"}]
        return " ".join(words[:6]) if words else research_question

    def process(self, request: LiteratureRequest) -> LiteratureResponse:
        uploaded_summaries: List[PaperSummary] = []
        discovered_papers: List[PaperSummary] = []

        # ----------------------------------------------------------------------
        # 1. Process Uploaded Papers (if any)
        # ----------------------------------------------------------------------
        for file_meta in request.uploaded_files:
            text_path = file_meta.extracted_text_path
            
            # Robust path resolution across potential directory prefixes
            if text_path and not os.path.exists(text_path):
                filename_base = os.path.basename(text_path)
                candidates = [
                    os.path.join(settings.UPLOAD_DIR, filename_base),
                    os.path.join("uploads", filename_base),
                    os.path.join("backend", "uploads", filename_base),
                    os.path.join(os.path.dirname(__file__), "..", "..", "uploads", filename_base)
                ]
                for candidate in candidates:
                    if os.path.exists(candidate):
                        text_path = candidate
                        break

            if not text_path or not os.path.exists(text_path):
                logger.warning(f"No extracted text found for {file_meta.filename}")
                uploaded_summaries.append(PaperSummary(
                    filename=file_meta.filename,
                    title=file_meta.filename,
                    source_type="uploaded",
                    source="uploaded",
                    summary="No text could be extracted from this file, or it was not uploaded properly.",
                    important_points=["Check file format or contents."]
                ))
                continue
                
            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Truncate content to fit in context window (safe margin for Qwen-8B)
                max_chars = 10000 
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n...[CONTENT TRUNCATED]..."

                prompt = self.uploaded_paper_prompt.format(
                    research_question=request.research_question,
                    paper_content=content
                )
                
                response_dict = local_llm_service.generate_json_response(prompt)
                
                summary = PaperSummary(
                    filename=file_meta.filename,
                    title=file_meta.filename,
                    source_type="uploaded",
                    source="uploaded",
                    summary=response_dict.get("summary", "No summary generated."),
                    important_points=response_dict.get("important_points", [])
                )
                uploaded_summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to process literature for {file_meta.filename}: {e}")
                summary = PaperSummary(
                    filename=file_meta.filename,
                    title=file_meta.filename,
                    source_type="uploaded",
                    source="uploaded",
                    summary=f"Failed to process this document. Error: {str(e)}",
                    important_points=["Document could not be analyzed."]
                )
                uploaded_summaries.append(summary)

        # ----------------------------------------------------------------------
        # 2. Search Academic Sources (Filtered to User-Selected Checkboxes)
        # ----------------------------------------------------------------------
        max_web_results = request.max_web_results or 4
        selected_sources = request.sources if request.sources else ["arxiv", "pubmed", "openalex", "crossref"]
        logger.info(f"Filtering search to user selected sources: {selected_sources}")

        try:
            search_query = self.generate_search_query(request.research_question)
            logger.info(f"Generated academic search query: '{search_query}'")
            
            raw_papers = academic_search_service.search(
                query=search_query,
                sources=selected_sources,
                max_total_results=max_web_results
            )

            # If specific search query yielded nothing, retry with raw question terms
            if not raw_papers and search_query != request.research_question:
                logger.info("Retrying search with raw research question terms...")
                raw_papers = academic_search_service.search(
                    query=request.research_question,
                    sources=selected_sources,
                    max_total_results=max_web_results
                )

            for paper in raw_papers:
                source_name = paper.get("source", "academic repository").upper()
                try:
                    prompt = self.web_paper_prompt.format(
                        source_name=source_name,
                        research_question=request.research_question,
                        paper_title=paper["title"],
                        abstract=paper["abstract"]
                    )
                    llm_res = local_llm_service.generate_json_response(prompt)
                    
                    paper_summary = PaperSummary(
                        filename=paper["title"],
                        title=paper["title"],
                        source_type="web_discovered",
                        source=paper.get("source", "web"),
                        url=paper.get("url"),
                        pdf_url=paper.get("pdf_url"),
                        authors=paper.get("authors", []),
                        year=paper.get("year"),
                        summary=llm_res.get("summary", paper["abstract"][:400] + "..."),
                        important_points=llm_res.get("important_points", [
                            f"Source: {source_name}",
                            f"Category: {paper.get('primary_category', 'Scientific Literature')}",
                            f"Year: {paper.get('year', 'Recent')}"
                        ])
                    )
                except Exception as e:
                    logger.warning(f"LLM analysis failed for {source_name} paper '{paper['title']}': {e}. Using abstract fallback.")
                    paper_summary = PaperSummary(
                        filename=paper["title"],
                        title=paper["title"],
                        source_type="web_discovered",
                        source=paper.get("source", "web"),
                        url=paper.get("url"),
                        pdf_url=paper.get("pdf_url"),
                        authors=paper.get("authors", []),
                        year=paper.get("year"),
                        summary=paper["abstract"],
                        important_points=[
                            f"Indexed in: {source_name}",
                            f"Field: {paper.get('primary_category', 'Academic Literature')}",
                            f"Publication Year: {paper.get('year', 'N/A')}"
                        ]
                    )
                discovered_papers.append(paper_summary)
        except Exception as e:
            logger.error(f"Error during academic literature retrieval: {e}")

        # ----------------------------------------------------------------------
        # 3. Generate Cross-Literature Synthesis
        # ----------------------------------------------------------------------
        synthesis_text = ""
        all_papers = uploaded_summaries + discovered_papers
        if all_papers:
            try:
                paper_descriptions = "\n".join([
                    f"- [{p.source.upper() if p.source else 'DOC'}] {p.title or p.filename}: {p.summary[:200]}..."
                    for p in all_papers
                ])
                synth_prompt = self.synthesis_prompt.format(
                    research_question=request.research_question,
                    selected_sources=", ".join([s.upper() for s in selected_sources]),
                    paper_list=paper_descriptions
                )
                synth_res = local_llm_service.generate_json_response(synth_prompt)
                synthesis_text = synth_res.get("synthesis", "")
            except Exception as e:
                logger.warning(f"Synthesis generation failed: {e}")
                sources_str = ", ".join([s.capitalize() for s in selected_sources])
                if discovered_papers and uploaded_summaries:
                    synthesis_text = f"Analyzed {len(uploaded_summaries)} uploaded paper(s) and {len(discovered_papers)} web-discovered paper(s) from {sources_str} regarding '{request.research_question}'."
                elif discovered_papers:
                    synthesis_text = f"Retrieved and analyzed {len(discovered_papers)} related research papers from {sources_str} relevant to '{request.research_question}'."
                else:
                    synthesis_text = f"Analyzed {len(uploaded_summaries)} uploaded research paper(s)."

        all_summaries = uploaded_summaries + discovered_papers
        return LiteratureResponse(
            summaries=all_summaries,
            uploaded_summaries=uploaded_summaries,
            discovered_papers=discovered_papers,
            synthesis=synthesis_text
        )

literature_agent = LiteratureAgent()
