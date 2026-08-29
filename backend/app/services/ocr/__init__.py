import logging
from typing import Dict, Any
from app.services.ocr.base_ocr import BaseOCREngine
from app.services.ocr.tesseract_engine import TesseractOCREngine, LANGUAGE_CODE_MAP
from app.services.ocr.online_ocr_engine import OnlineOCREngine

logger = logging.getLogger(__name__)

tesseract_engine = TesseractOCREngine()
online_engine = OnlineOCREngine()

def run_online_ocr(file_path: str, language: str = "English") -> str:
    res = online_engine.extract_text(file_path, language)
    return res.get("text", "")

def run_ocr(file_path: str, language: str = "English") -> Dict[str, Any]:
    """
    Standard OCR entry point:
    Attempts local Tesseract OCR with multi-language packs.
    If Tesseract is unavailable or errors, falls back to OCR.space online engine.
    """
    try:
        return tesseract_engine.extract_text(file_path, language)
    except Exception as e:
        logger.warning(f"Local Tesseract OCR unavailable: {str(e)}. Falling back to online OCR API.")
        return online_engine.extract_text(file_path, language)

__all__ = [
    "BaseOCREngine",
    "TesseractOCREngine",
    "OnlineOCREngine",
    "LANGUAGE_CODE_MAP",
    "run_ocr",
    "run_online_ocr"
]
