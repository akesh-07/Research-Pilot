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
        self.uploaded_paper_prompt = """You are the Literature Search Agent of ResearchPilot, strictly and exclusively specialized in pharmaceutical, biomedical, and computational drug discovery.

CRITICAL USER QUERY ADHERENCE DIRECTIVE:
Your analysis, summary, and extracted points MUST be strictly and exclusively relevant to what the user specifically wants to research:
User's Specific Research Question: "{research_question}"

INSTRUCTIONS:
1. Analyze the provided document ONLY through the perspective of how it answers, supports, or informs the User's Specific Research Question.
2. DO NOT include general paper trivia, peripheral study background, or unrelated findings from the paper.
3. In "summary": State clearly and specifically how this paper directly informs or answers the User's Research Question ("{research_question}"). Highlight specific biological targets, chemical entities, binding affinities, or mechanisms directly pertinent to what the user asked.
4. In "important_points": Extract 3 to 5 key points that directly answer or provide actionable evidence for "{research_question}". Every single bullet point must directly relate to the user's research focus.

User's Specific Research Question: {research_question}

Paper Content:
{paper_content}

Return valid JSON only in the following format:
{{
  "summary": "Concise, high-density summary explaining specifically how this paper informs or answers the user's research question regarding {research_question}...",
  "important_points": [
    "Specific finding directly relevant to the user's research question...",
    "Identified target, chemical scaffold, or mechanism addressing the user's question...",
    "Quantitative assay result (IC50, Kd, Ki), selectivity, or ADMET data addressing the user's question...",
    "Methodological insight or limitation directly impacting the user's research goal..."
  ]
}}
"""

        self.web_paper_prompt = """You are the Literature Search Agent of ResearchPilot, strictly dedicated to pharmaceutical, biochemical, and computational drug discovery.

CRITICAL USER QUERY ADHERENCE DIRECTIVE:
Your analysis, summary, and extracted points MUST be strictly and exclusively anchored to the User's Specific Research Question:
User's Specific Research Question: "{research_question}"

INSTRUCTIONS:
1. Critically examine the academic paper abstract retrieved from {source_name} ONLY for information that directly addresses, answers, or provides evidence for the user's specific inquiry.
2. DO NOT produce a generic summary of the abstract. Filter out all irrelevant or tangential context.
3. In "summary": Explicitly describe how this study's findings directly address or inform the user's question regarding "{research_question}". Identify relevant molecular targets, chemical compounds, mechanisms of action, or therapeutic insights.
4. In "important_points": Extract 3 key bullet points that provide direct scientific answers, assay data, or experimental methodologies relevant to what the user asked.

User's Specific Research Question: {research_question}

Paper Title: {paper_title}
Source: {source_name}
Abstract:
{abstract}

Return valid JSON only in the following format:
{{
  "summary": "Summary strictly focused on what this paper reveals regarding the user's specific research question: {research_question}...",
  "important_points": [
    "Key finding or biological mechanism directly informing the user's inquiry...",
    "Candidate chemical entity, modeling technique, or assay result relevant to the user's inquiry...",
    "Pharmacological relevance or actionable outcome directly addressing what the user wants to know..."
  ]
}}
"""

        self.synthesis_prompt = """You are the Literature Search Agent of ResearchPilot, strictly specialized in pharmaceutical drug discovery intelligence.

CRITICAL USER QUERY ADHERENCE DIRECTIVE:
You must synthesize the analyzed literature STRICTLY AND EXCLUSIVELY to answer what the user specifically asked in their research question:
User's Specific Research Question: "{research_question}"

INSTRUCTIONS:
1. Synthesize the collected literature into a cohesive, rigorous scientific analysis focused entirely on answering "{research_question}".
2. DO NOT provide a vague or generalized overview. Directly address what the evidence reveals about the specific target, disease, chemical scaffolds, or mechanisms the user asked about.
3. Compare the methodologies (in silico screening, molecular dynamics, in vitro assays) reported in the papers specifically applied to the user's question.
4. Highlight concrete findings: validated candidate molecules, binding potencies, confirmed mechanisms of action, and contradictory or unaddressed challenges directly related to "{research_question}".
5. Conclude with specific, actionable opportunities to solve or advance the user's exact research objective.

User's Specific Research Question: {research_question}
Analyzed Papers from Selected Sources ({selected_sources}):
{paper_list}

Return valid JSON only in the following format:
{{
  "synthesis": "An in-depth, rigorous scientific synthesis directly answering the user's research question regarding {research_question}, comparing methodologies across retrieved papers, synthesizing identified targets and chemical leads, and highlighting open therapeutic opportunities specifically for this inquiry."
}}
"""

    def generate_search_query(self, research_question: str) -> str:
        """Derive an effective academic search query from the research question."""
        prompt = f"""You are an expert biomedical research assistant strictly specialized in pharmaceutical drug discovery and medicinal chemistry.

CRITICAL KEYWORD EXTRACTION DIRECTIVE:
Extract 3 to 6 essential academic keywords directly derived from the user's specific research question.
The keywords MUST strictly target the exact disease, biological target, chemical class, or therapeutic mechanism requested by the user.
- DO NOT add external or unrequested diseases or drugs.
- Prioritize high-specificity terms (e.g., target protein names, specific mutations, disease nomenclature, mechanism of action, or screening method) present in or directly implied by the question.
- Do not use boolean operators, quotes, or punctuation.

User's Specific Research Question: {research_question}

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
                    f"- [{p.source.upper() if p.source else 'DOC'}] {p.title or p.filename}: {p.summary[:600]}..."
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
