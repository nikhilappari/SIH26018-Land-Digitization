import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def extract_pdf_pages_or_text(pdf_path: str) -> dict:
    """
    Extracts text and metadata from PDF files.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        extracted_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                extracted_text.append(text)
        
        full_text = "\n".join(extracted_text)
        return {
            "num_pages": len(reader.pages),
            "text": full_text.strip(),
            "has_embedded_text": len(full_text.strip()) > 20
        }
    except Exception as e:
        logger.warning(f"PDF processing error for {pdf_path}: {str(e)}")
        return {
            "num_pages": 1,
            "text": "",
            "has_embedded_text": False
        }
