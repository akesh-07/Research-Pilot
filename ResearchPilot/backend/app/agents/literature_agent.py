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
        # ── BATCH PROMPT: all uploaded documents in one call ──────────────────
        self.batch_uploaded_prompt = """You are the Literature Search Agent of ResearchPilot, strictly and exclusively specialized in pharmaceutical, biomedical, and computational drug discovery.

CRITICAL USER QUERY ADHERENCE DIRECTIVE:
Every analysis MUST be strictly and exclusively relevant to the User's Specific Research Question:
"{research_question}"

You are given {n_docs} uploaded research documents below, each separated by "=== DOCUMENT [index] ===".
For EACH document produce a focused analysis object.

INSTRUCTIONS (apply to every document independently):
1. Analyse the document ONLY through the lens of how it answers or informs "{research_question}".
2. DO NOT include general paper trivia or findings unrelated to the question.
3. "summary": How this document directly informs the research question — specific targets, chemical entities, affinities, mechanisms.
4. "important_points": 3 to 5 bullet points that directly answer or provide actionable evidence for the question.

Documents:
{documents_block}

Return a JSON array with exactly {n_docs} objects, in the same order as the documents:
[
  {{
    "index": 0,
    "summary": "...",
    "important_points": ["...", "..."]
  }},
  ...
]
"""

        # ── BATCH PROMPT: all web-discovered papers in one call ────────────────
        self.batch_web_prompt = """You are the Literature Search Agent of ResearchPilot, strictly dedicated to pharmaceutical, biochemical, and computational drug discovery.

CRITICAL USER QUERY ADHERENCE DIRECTIVE:
Every analysis MUST be strictly and exclusively anchored to the User's Specific Research Question:
"{research_question}"

You are given {n_papers} academic paper abstracts below, each separated by "=== PAPER [index] ===".
For EACH paper produce a focused analysis object.

INSTRUCTIONS (apply to every paper independently):
1. Examine the abstract ONLY for information that directly addresses "{research_question}".
2. DO NOT produce a generic summary. Filter out all irrelevant context.
3. "summary": How this paper's findings directly address the question — molecular targets, compounds, MoA, therapeutic insights.
4. "important_points": Exactly 3 bullet points — key findings, assay data, or methodologies relevant to the question.

Papers:
{papers_block}

Return a JSON array with exactly {n_papers} objects, in the same order as the papers:
[
  {{
    "index": 0,
    "summary": "...",
    "important_points": ["...", "..."]
  }},
  ...
]
"""

        # ── SINGLE-PAPER FALLBACK PROMPTS (used only on batch parse failure) ──
        self.uploaded_paper_prompt = """You are the Literature Search Agent of ResearchPilot, strictly and exclusively specialized in pharmaceutical, biomedical, and computational drug discovery.

User's Specific Research Question: "{research_question}"

Analyse the document ONLY through the lens of how it answers "{research_question}".
In "summary": how this paper directly informs the question.
In "important_points": 3–5 key points directly answering the question.

Paper Content:
{paper_content}

Return valid JSON only:
{{
  "summary": "...",
  "important_points": ["...", "...", "..."]
}}
"""

        self.web_paper_prompt = """You are the Literature Search Agent of ResearchPilot, strictly dedicated to pharmaceutical, biochemical, and computational drug discovery.

User's Specific Research Question: "{research_question}"

Examine the abstract from {source_name} ONLY for information directly addressing "{research_question}".
In "summary": how this study's findings address the question.
In "important_points": exactly 3 key bullet points.

Paper Title: {paper_title}
Source: {source_name}
Abstract:
{abstract}

Return valid JSON only:
{{
  "summary": "...",
  "important_points": ["...", "...", "..."]
}}
"""

        self.synthesis_prompt = """You are the Literature Search Agent of ResearchPilot, strictly specialized in pharmaceutical drug discovery intelligence.

User's Specific Research Question: "{research_question}"

Synthesize the collected literature STRICTLY to answer "{research_question}":
1. Rigorous scientific analysis focused entirely on answering the question.
2. Compare methodologies (in silico, MD, in vitro) applied to the question.
3. Highlight concrete findings: validated molecules, binding potencies, mechanisms, contradictions.
4. Conclude with specific actionable opportunities for the user's exact objective.

Analyzed Papers from Selected Sources ({selected_sources}):
{paper_list}

Return valid JSON only:
{{
  "synthesis": "An in-depth, rigorous scientific synthesis directly answering the user's research question regarding {research_question}, comparing methodologies, synthesizing chemical leads, and highlighting open therapeutic opportunities."
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_text_path(self, file_meta) -> str | None:
        """Return a valid extracted-text path for an uploaded file, or None."""
        text_path = file_meta.extracted_text_path
        if text_path and os.path.exists(text_path):
            return text_path
        if text_path:
            filename_base = os.path.basename(text_path)
            candidates = [
                os.path.join(settings.UPLOAD_DIR, filename_base),
                os.path.join("uploads", filename_base),
                os.path.join("backend", "uploads", filename_base),
                os.path.join(os.path.dirname(__file__), "..", "..", "uploads", filename_base),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    return candidate
        return None

    def _read_truncated(self, path: str, max_chars: int = 6000) -> str:
        """Read a file and truncate to max_chars so multiple docs fit in one prompt."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > max_chars:
            content = content[:max_chars] + "\n...[CONTENT TRUNCATED]..."
        return content

    def _parse_batch_response(self, raw: list | dict, expected: int) -> list[dict]:
        """
        Normalise whatever the LLM returned into a list of dicts.
        raw may be a list already, or a dict with a key wrapping the list.
        Falls back to an empty list so callers can detect failure.
        """
        if isinstance(raw, list):
            return raw
        # Some models wrap the array under a key like {"results": [...]}
        if isinstance(raw, dict):
            for v in raw.values():
                if isinstance(v, list):
                    return v
        return []

    # ------------------------------------------------------------------
    # Batch processing – uploaded documents
    # ------------------------------------------------------------------

    def _process_uploaded_batch(self, request, file_metas_with_content: list[tuple]) -> List[PaperSummary]:
        """
        Send all readable uploaded documents to the LLM in a single call.
        file_metas_with_content: list of (file_meta, content_str) tuples.
        """
        if not file_metas_with_content:
            return []

        n = len(file_metas_with_content)
        documents_block = ""
        for i, (fm, content) in enumerate(file_metas_with_content):
            documents_block += f"=== DOCUMENT {i} ===\nFilename: {fm.filename}\n{content}\n\n"

        prompt = self.batch_uploaded_prompt.format(
            research_question=request.research_question,
            n_docs=n,
            documents_block=documents_block.strip(),
        )

        try:
            raw = local_llm_service.generate_json_response(prompt)
            results = self._parse_batch_response(raw, n)
            if len(results) != n:
                raise ValueError(f"Expected {n} results, got {len(results)}")

            summaries = []
            for i, (fm, _) in enumerate(file_metas_with_content):
                r = results[i] if i < len(results) else {}
                summaries.append(PaperSummary(
                    filename=fm.filename,
                    title=fm.filename,
                    source_type="uploaded",
                    source="uploaded",
                    summary=r.get("summary", "No summary generated."),
                    important_points=r.get("important_points", []),
                ))
            logger.info(f"Batch uploaded: processed {n} document(s) in 1 LLM call.")
            return summaries

        except Exception as e:
            logger.warning(f"Batch uploaded processing failed ({e}). Falling back to per-document calls.")
            return self._process_uploaded_individually(request, file_metas_with_content)

    def _process_uploaded_individually(self, request, file_metas_with_content: list[tuple]) -> List[PaperSummary]:
        """Per-document fallback used only when batch parsing fails."""
        summaries = []
        for fm, content in file_metas_with_content:
            try:
                prompt = self.uploaded_paper_prompt.format(
                    research_question=request.research_question,
                    paper_content=content,
                )
                r = local_llm_service.generate_json_response(prompt)
                summaries.append(PaperSummary(
                    filename=fm.filename, title=fm.filename,
                    source_type="uploaded", source="uploaded",
                    summary=r.get("summary", "No summary generated."),
                    important_points=r.get("important_points", []),
                ))
            except Exception as e:
                logger.error(f"Fallback individual upload failed for {fm.filename}: {e}")
                summaries.append(PaperSummary(
                    filename=fm.filename, title=fm.filename,
                    source_type="uploaded", source="uploaded",
                    summary=f"Failed to process this document. Error: {str(e)}",
                    important_points=["Document could not be analyzed."],
                ))
        return summaries

    # ------------------------------------------------------------------
    # Batch processing – web-discovered papers
    # ------------------------------------------------------------------

    def _process_web_batch(self, request, raw_papers: list) -> List[PaperSummary]:
        """
        Send all web-discovered paper abstracts to the LLM in a single call.
        """
        if not raw_papers:
            return []

        n = len(raw_papers)
        papers_block = ""
        for i, paper in enumerate(raw_papers):
            source_name = paper.get("source", "academic repository").upper()
            papers_block += (
                f"=== PAPER {i} ===\n"
                f"Title: {paper['title']}\n"
                f"Source: {source_name}\n"
                f"Abstract: {paper['abstract']}\n\n"
            )

        prompt = self.batch_web_prompt.format(
            research_question=request.research_question,
            n_papers=n,
            papers_block=papers_block.strip(),
        )

        try:
            raw = local_llm_service.generate_json_response(prompt)
            results = self._parse_batch_response(raw, n)
            if len(results) != n:
                raise ValueError(f"Expected {n} results, got {len(results)}")

            summaries = []
            for i, paper in enumerate(raw_papers):
                source_name = paper.get("source", "web").upper()
                r = results[i] if i < len(results) else {}
                summaries.append(PaperSummary(
                    filename=paper["title"],
                    title=paper["title"],
                    source_type="web_discovered",
                    source=paper.get("source", "web"),
                    url=paper.get("url"),
                    pdf_url=paper.get("pdf_url"),
                    authors=paper.get("authors", []),
                    year=paper.get("year"),
                    summary=r.get("summary", paper["abstract"][:400] + "..."),
                    important_points=r.get("important_points", [
                        f"Source: {source_name}",
                        f"Category: {paper.get('primary_category', 'Scientific Literature')}",
                        f"Year: {paper.get('year', 'Recent')}",
                    ]),
                ))
            logger.info(f"Batch web: processed {n} paper(s) in 1 LLM call.")
            return summaries

        except Exception as e:
            logger.warning(f"Batch web processing failed ({e}). Falling back to per-paper calls.")
            return self._process_web_individually(request, raw_papers)

    def _process_web_individually(self, request, raw_papers: list) -> List[PaperSummary]:
        """Per-paper fallback used only when batch parsing fails."""
        summaries = []
        for paper in raw_papers:
            source_name = paper.get("source", "academic repository").upper()
            try:
                prompt = self.web_paper_prompt.format(
                    source_name=source_name,
                    research_question=request.research_question,
                    paper_title=paper["title"],
                    abstract=paper["abstract"],
                )
                r = local_llm_service.generate_json_response(prompt)
                summaries.append(PaperSummary(
                    filename=paper["title"], title=paper["title"],
                    source_type="web_discovered", source=paper.get("source", "web"),
                    url=paper.get("url"), pdf_url=paper.get("pdf_url"),
                    authors=paper.get("authors", []), year=paper.get("year"),
                    summary=r.get("summary", paper["abstract"][:400] + "..."),
                    important_points=r.get("important_points", [
                        f"Source: {source_name}",
                        f"Category: {paper.get('primary_category', 'Scientific Literature')}",
                        f"Year: {paper.get('year', 'Recent')}",
                    ]),
                ))
            except Exception as e:
                logger.warning(f"Fallback per-paper failed for '{paper['title']}': {e}. Using abstract.")
                summaries.append(PaperSummary(
                    filename=paper["title"], title=paper["title"],
                    source_type="web_discovered", source=paper.get("source", "web"),
                    url=paper.get("url"), pdf_url=paper.get("pdf_url"),
                    authors=paper.get("authors", []), year=paper.get("year"),
                    summary=paper["abstract"],
                    important_points=[
                        f"Indexed in: {source_name}",
                        f"Field: {paper.get('primary_category', 'Academic Literature')}",
                        f"Publication Year: {paper.get('year', 'N/A')}",
                    ],
                ))
        return summaries

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def process(self, request: LiteratureRequest) -> LiteratureResponse:
        uploaded_summaries: List[PaperSummary] = []
        discovered_papers: List[PaperSummary] = []

        # ── 1. Collect readable uploaded documents ──────────────────────────
        readable_uploads: list[tuple] = []   # (file_meta, content_str)
        for file_meta in request.uploaded_files:
            text_path = self._resolve_text_path(file_meta)
            if not text_path:
                logger.warning(f"No extracted text found for {file_meta.filename}")
                uploaded_summaries.append(PaperSummary(
                    filename=file_meta.filename,
                    title=file_meta.filename,
                    source_type="uploaded",
                    source="uploaded",
                    summary="No text could be extracted from this file, or it was not uploaded properly.",
                    important_points=["Check file format or contents."],
                ))
                continue
            # Per-doc char budget: keep total batch ≤ ~24 000 chars for Qwen-8B
            content = self._read_truncated(text_path, max_chars=6000)
            readable_uploads.append((file_meta, content))

        # ── 2. Batch-process uploaded documents (1 LLM call) ───────────────
        if readable_uploads:
            uploaded_summaries.extend(
                self._process_uploaded_batch(request, readable_uploads)
            )

        # ── 3. Search academic sources ─────────────────────────────────────
        max_web_results = request.max_web_results or 4
        selected_sources = request.sources if request.sources else ["arxiv", "pubmed", "openalex", "crossref"]
        logger.info(f"Filtering search to user selected sources: {selected_sources}")
        raw_papers: list = []

        try:
            search_query = self.generate_search_query(request.research_question)
            logger.info(f"Generated academic search query: '{search_query}'")

            raw_papers = academic_search_service.search(
                query=search_query,
                sources=selected_sources,
                max_total_results=max_web_results,
            )

            if not raw_papers and search_query != request.research_question:
                logger.info("Retrying search with raw research question terms...")
                raw_papers = academic_search_service.search(
                    query=request.research_question,
                    sources=selected_sources,
                    max_total_results=max_web_results,
                )
        except Exception as e:
            logger.error(f"Error during academic literature retrieval: {e}")

        # ── 4. Batch-process web papers (1 LLM call) ───────────────────────
        if raw_papers:
            discovered_papers.extend(
                self._process_web_batch(request, raw_papers)
            )

        # ── 5. Cross-literature synthesis (1 LLM call) ────────────────────
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
                    paper_list=paper_descriptions,
                )
                synth_res = local_llm_service.generate_json_response(synth_prompt)
                synthesis_text = synth_res.get("synthesis", "")
            except Exception as e:
                logger.warning(f"Synthesis generation failed: {e}")
                sources_str = ", ".join([s.capitalize() for s in selected_sources])
                if discovered_papers and uploaded_summaries:
                    synthesis_text = (
                        f"Analyzed {len(uploaded_summaries)} uploaded paper(s) and "
                        f"{len(discovered_papers)} web-discovered paper(s) from {sources_str} "
                        f"regarding '{request.research_question}'."
                    )
                elif discovered_papers:
                    synthesis_text = (
                        f"Retrieved and analyzed {len(discovered_papers)} related research papers "
                        f"from {sources_str} relevant to '{request.research_question}'."
                    )
                else:
                    synthesis_text = f"Analyzed {len(uploaded_summaries)} uploaded research paper(s)."

        return LiteratureResponse(
            summaries=uploaded_summaries + discovered_papers,
            uploaded_summaries=uploaded_summaries,
            discovered_papers=discovered_papers,
            synthesis=synthesis_text,
        )

literature_agent = LiteratureAgent()
