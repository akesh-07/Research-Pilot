import requests
import re
from typing import List, Dict
from app.core.logging import logger

class CrossrefService:
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"
        self.headers = {
            "User-Agent": "ResearchPilot/1.0 (mailto:researchpilot.platform@gmail.com)"
        }

    def clean_abstract(self, raw_abstract: str) -> str:
        if not raw_abstract:
            return ""
        # Strip JATS or XML tags like <jats:p>, <jats:sec>, etc.
        cleaned = re.sub(r'<[^>]+>', ' ', raw_abstract)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def search_papers(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search Crossref (150M+ formal publisher records & DOIs, no API key required) and return papers.
        """
        cleaned = re.sub(r'[\?\!\:\;\,\"\']', ' ', query).strip()
        logger.info(f"Searching Crossref for: '{cleaned}' (max_results={max_results})")

        try:
            params = {
                "query": cleaned,
                "rows": max_results,
                "sort": "relevance"
            }
            res = requests.get(self.base_url, params=params, headers=self.headers, timeout=8)
            if res.status_code != 200:
                logger.warning(f"Crossref returned status code {res.status_code}")
                return []

            data = res.json()
            items = data.get("message", {}).get("items", [])
            papers = []

            for item in items:
                title_list = item.get("title", [])
                title = title_list[0] if title_list else None
                if not title:
                    continue

                # Authors
                authors = []
                for auth in item.get("author", []):
                    name = f"{auth.get('given', '')} {auth.get('family', '')}".strip()
                    if name:
                        authors.append(name)
                if len(authors) > 3:
                    authors = authors[:3] + ["et al."]

                # Year
                year = None
                date_parts = item.get("published", {}).get("date-parts", [[]])
                if date_parts and date_parts[0]:
                    year = date_parts[0][0]

                # Abstract
                abstract = self.clean_abstract(item.get("abstract", ""))
                if not abstract:
                    container = item.get("container-title", [""])[0] if item.get("container-title") else "Academic Journal"
                    abstract = f"Published in {container}. Full text and references indexed via Crossref DOI registry."

                # URL
                url = item.get("URL") or (f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else None)

                # PDF Link if available
                pdf_url = None
                links = item.get("link", [])
                for l in links:
                    if "pdf" in l.get("content-type", "").lower():
                        pdf_url = l.get("URL")
                        break

                publisher = item.get("publisher", "Peer-Reviewed Journal")

                papers.append({
                    "title": title.strip(),
                    "authors": authors,
                    "year": year,
                    "url": url,
                    "pdf_url": pdf_url,
                    "abstract": abstract.strip(),
                    "source": "crossref",
                    "primary_category": publisher
                })

            logger.info(f"Retrieved {len(papers)} papers from Crossref.")
            return papers
        except Exception as e:
            logger.error(f"Error querying Crossref: {e}")
            return []

crossref_service = CrossrefService()
