import arxiv
import re
from typing import List, Dict
from app.core.logging import logger

class ArxivService:
    def __init__(self):
        self.client = arxiv.Client(
            page_size=5,
            delay_seconds=3,
            num_retries=3
        )

    def clean_query(self, raw_query: str) -> str:
        # Strip common punctuation that might disrupt arXiv boolean search
        cleaned = re.sub(r'[\?\!\.\:\;\,\"\']', ' ', raw_query)
        # Collapse multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Limit query terms length to keep arXiv search effective
        words = cleaned.split()
        if len(words) > 10:
            words = words[:10]
        return " ".join(words)

    def search_papers(self, query: str, max_results: int = 4) -> List[Dict]:
        """
        Search arXiv for relevant scientific papers and return structured metadata.
        """
        cleaned_query = self.clean_query(query)
        logger.info(f"Searching arXiv for: '{cleaned_query}' (max_results={max_results})")
        
        try:
            search = arxiv.Search(
                query=cleaned_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in self.client.results(search):
                authors = [author.name for author in result.authors[:4]]
                if len(result.authors) > 4:
                    authors.append("et al.")

                # Clean abstract whitespace and newlines
                abstract = re.sub(r'\s+', ' ', result.summary).strip()
                title = re.sub(r'\s+', ' ', result.title).strip()

                papers.append({
                    "title": title,
                    "authors": authors,
                    "year": result.published.year if result.published else None,
                    "url": result.entry_id,
                    "pdf_url": result.pdf_url,
                    "abstract": abstract,
                    "primary_category": result.primary_category
                })

            logger.info(f"Retrieved {len(papers)} papers from arXiv.")
            return papers
        except Exception as e:
            logger.error(f"Error querying arXiv: {e}")
            return []

arxiv_service = ArxivService()
