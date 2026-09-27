import logging
import pymupdf
from typing import List, Dict, Any
from app.rag.cleaner import clean_text

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file using PyMuPDF, preserving page numbers.
    Returns a list of dictionaries containing page text and metadata.
    """
    extracted_pages = []
    try:
        with pymupdf.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                raw_text = page.get_text("text")
                cleaned = clean_text(raw_text)
                
                if cleaned:
                    extracted_pages.append({
                        "page_number": page_num + 1,
                        "text": cleaned,
                        "char_count": len(cleaned)
                    })
        logger.info(f"Extracted {len(extracted_pages)} pages from {file_path}")
        return extracted_pages
    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        return []