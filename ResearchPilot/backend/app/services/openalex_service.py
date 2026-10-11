import requests
import re
from typing import List, Dict
from app.core.logging import logger

class OpenAlexService:
    def __init__(self):
        self.base_url = "https://api.openalex.org/works"
        self.headers = {
            "User-Agent": "ResearchPilot/1.0 (mailto:researchpilot.platform@gmail.com)"
        }

    def reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract string from OpenAlex inverted index representation."""
        if not inverted_index:
            return ""
        try:
            positions = []
            for word, indices in inverted_index.items():
                for idx in indices:
                    positions.append((idx, word))
            positions.sort(key=lambda x: x[0])
            return " ".join([word for _, word in positions])
        except Exception:
            return ""

    def search_papers(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search OpenAlex (250M+ open catalog works, no API key required) and return papers.
        """
        cleaned = re.sub(r'[\?\!\:\;\,\"\']', ' ', query).strip()
        logger.info(f"Searching OpenAlex for: '{cleaned}' (max_results={max_results})")
        
        try:
            params = {
                "search": cleaned,
                "per_page": max_results,
                "sort": "relevance_score:desc"
            }
            res = requests.get(self.base_url, params=params, headers=self.headers, timeout=8)
            if res.status_code != 200:
                logger.warning(f"OpenAlex returned status code {res.status_code}")
                return []

            data = res.json()
            results = data.get("results", [])
            papers = []

            for work in results:
                title = work.get("title")
                if not title:
                    continue

                # Reconstruct Abstract
                abstract = self.reconstruct_abstract(work.get("abstract_inverted_index"))
                if not abstract:
                    abstract = "No detailed abstract provided in OpenAlex index."

                # Extract Authors
                authors = []
                for auth_obj in work.get("authorships", []):
                    display_name = auth_obj.get("author", {}).get("display_name")
                    if display_name:
                        authors.append(display_name)
                if len(authors) > 3:
                    authors = authors[:3] + ["et al."]

                # Link / PDF
                doi = work.get("doi")
                url = doi if doi else work.get("id")
                pdf_url = work.get("primary_location", {}).get("pdf_url") or (work.get("open_access", {}).get("oa_url"))

                # Primary Concept / Category
                concepts = work.get("concepts", [])
                primary_category = concepts[0].get("display_name") if concepts else "Multidisciplinary Science"

                papers.append({
                    "title": title.strip(),
                    "authors": authors,
                    "year": work.get("publication_year"),
                    "url": url,
                    "pdf_url": pdf_url,
                    "abstract": abstract.strip(),
                    "source": "openalex",
                    "primary_category": primary_category
                })

            logger.info(f"Retrieved {len(papers)} papers from OpenAlex.")
            return papers
        except Exception as e:
            logger.error(f"Error querying OpenAlex: {e}")
            return []

openalex_service = OpenAlexService()
