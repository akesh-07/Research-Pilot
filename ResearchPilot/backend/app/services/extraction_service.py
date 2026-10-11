import fitz  # PyMuPDF
from docx import Document
import os
from app.core.logging import logger

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text accurately from a PDF file."""
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a Word document."""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX {file_path}: {e}")
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extracts text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to extract text from TXT {file_path}: {e}")
        return ""

def extract_content(file_path: str, ext: str) -> str:
    """Routes to the appropriate extractor based on extension."""
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        logger.warning(f"Unsupported extension for extraction: {ext}")
        return ""
