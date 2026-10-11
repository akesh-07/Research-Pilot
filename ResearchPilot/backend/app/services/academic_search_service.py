import re
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.logging import logger
from app.services.arxiv_service import arxiv_service
from app.services.pubmed_service import pubmed_service
from app.services.openalex_service import openalex_service
from app.services.crossref_service import crossref_service

AVAILABLE_SOURCES = {
    "arxiv": {"name": "arXiv", "service": arxiv_service},
    "pubmed": {"name": "PubMed", "service": pubmed_service},
    "openalex": {"name": "OpenAlex", "service": openalex_service},
    "crossref": {"name": "Crossref", "service": crossref_service}
}

class AcademicSearchService:
    def __init__(self):
        pass

    def _normalize_title(self, title: str) -> str:
        """Strip non-alphanumeric characters for deduplication comparison."""
        return re.sub(r'[^a-zA-Z0-9]', '', title).lower()

    def search(self, query: str, sources: List[str] = None, max_total_results: int = 4) -> List[Dict]:
        """
        Search only the specified academic sources concurrently.
        """
        if not sources:
            sources = ["arxiv", "pubmed", "openalex", "crossref"]

        # Filter valid and requested sources
        selected_keys = [s.strip().lower() for s in sources if s.strip().lower() in AVAILABLE_SOURCES]
        if not selected_keys:
            selected_keys = ["arxiv"]  # Fallback

        logger.info(f"Executing multi-source academic search for sources: {selected_keys}")

        # Distribute items per source so we don't overwhelm LLM context
        # e.g., if 2 sources selected and max_total is 4, get 2 from each.
        per_source = max(1, (max_total_results // len(selected_keys)) + 1)

        results: List[Dict] = []
        futures = {}

        with ThreadPoolExecutor(max_workers=min(len(selected_keys), 4)) as executor:
            for source_key in selected_keys:
                service = AVAILABLE_SOURCES[source_key]["service"]
                # In arxiv_service, ensure 'source' key is populated
                def fetch_source(s_key, s_service):
                    papers = s_service.search_papers(query, max_results=per_source)
                    for p in papers:
                        if "source" not in p:
                            p["source"] = s_key
                    return papers

                future = executor.submit(fetch_source, source_key, service)
                futures[future] = source_key

            for future in as_completed(futures):
                source_key = futures[future]
                try:
                    papers = future.result()
                    results.extend(papers)
                except Exception as e:
                    logger.error(f"Error fetching from academic source {source_key}: {e}")

        # Deduplicate papers based on title similarity
        seen_titles = set()
        deduplicated = []
        for paper in results:
            norm_title = self._normalize_title(paper.get("title", ""))
            if norm_title and norm_title not in seen_titles:
                seen_titles.add(norm_title)
                deduplicated.append(paper)

        # Cap to requested max
        capped_results = deduplicated[:max(max_total_results, len(selected_keys))]
        logger.info(f"Total deduplicated papers across {selected_keys}: {len(capped_results)}")
        return capped_results

academic_search_service = AcademicSearchService()
