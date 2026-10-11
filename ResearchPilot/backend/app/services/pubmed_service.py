import requests
import re
from typing import List, Dict
from xml.etree import ElementTree as ET
from app.core.logging import logger

class PubMedService:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.headers = {
            "User-Agent": "ResearchPilot/1.0 (academic-assistant)"
        }

    def clean_query(self, raw_query: str) -> str:
        cleaned = re.sub(r'[\?\!\:\;\,\"\']', ' ', raw_query)
        words = cleaned.split()
        return "+".join(words[:8]) if words else raw_query

    def search_papers(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search PubMed via NCBI E-Utilities (no API key required) and return papers.
        """
        cleaned = self.clean_query(query)
        logger.info(f"Searching PubMed for: '{cleaned}' (max_results={max_results})")
        
        try:
            # 1. Search for PMIDs
            esearch_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": cleaned,
                "retmode": "json",
                "retmax": max_results,
                "sort": "relevance"
            }
            res = requests.get(esearch_url, params=params, headers=self.headers, timeout=8)
            if res.status_code != 200:
                logger.warning(f"PubMed search returned status {res.status_code}")
                return []

            data = res.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                logger.info("PubMed returned 0 PMIDs.")
                return []

            # 2. Fetch Article Details (XML)
            efetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml"
            }
            fetch_res = requests.get(efetch_url, params=fetch_params, headers=self.headers, timeout=10)
            if fetch_res.status_code != 200:
                logger.warning(f"PubMed efetch returned status {fetch_res.status_code}")
                return []

            root = ET.fromstring(fetch_res.content)
            papers = []

            for article in root.findall(".//PubmedArticle"):
                pmid_el = article.find(".//MedlineCitation/PMID")
                pmid = pmid_el.text if pmid_el is not None else ""

                title_el = article.find(".//ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else "Untitled PubMed Article"

                # Extract Abstract
                abstract_parts = []
                for abs_text in article.findall(".//Abstract/AbstractText"):
                    abstract_parts.append("".join(abs_text.itertext()).strip())
                abstract = " ".join(abstract_parts).strip()
                if not abstract:
                    abstract = "No abstract available in PubMed record."

                # Extract Authors
                authors = []
                for author in article.findall(".//AuthorList/Author"):
                    last = author.find("LastName")
                    fore = author.find("ForeName")
                    if last is not None:
                        name = f"{fore.text} {last.text}" if fore is not None else last.text
                        authors.append(name)
                if len(authors) > 3:
                    authors = authors[:3] + ["et al."]

                # Extract Year
                year = None
                year_el = article.find(".//Journal/JournalIssue/PubDate/Year")
                if year_el is not None and year_el.text:
                    try:
                        year = int(year_el.text)
                    except ValueError:
                        pass
                if not year:
                    medline_date = article.find(".//Journal/JournalIssue/PubDate/MedlineDate")
                    if medline_date is not None and medline_date.text:
                        match = re.search(r'\b(19\d\d|20\d\d)\b', medline_date.text)
                        if match:
                            year = int(match.group(1))

                papers.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                    "pdf_url": None,
                    "abstract": abstract,
                    "source": "pubmed",
                    "primary_category": "Biomedicine / Health Sciences"
                })

            logger.info(f"Retrieved {len(papers)} papers from PubMed.")
            return papers
        except Exception as e:
            logger.error(f"Error querying PubMed: {e}")
            return []

pubmed_service = PubMedService()
