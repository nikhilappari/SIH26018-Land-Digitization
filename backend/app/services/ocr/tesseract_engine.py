import os
import pytesseract
from PIL import Image
import logging
from typing import Dict, Any
from app.services.ocr.base_ocr import BaseOCREngine

logger = logging.getLogger(__name__)

LANGUAGE_CODE_MAP = {
    "English": "eng",
    "Telugu": "tel+eng",
    "Hindi": "hin+eng",
    "Tamil": "tam+eng",
    "Kannada": "kan+eng",
    "Malayalam": "mal+eng",
    "Marathi": "mar+eng",
    "Bengali": "ben+eng",
    "Gujarati": "guj+eng",
    "Odia": "ori+eng",
    "Punjabi": "pan+eng",
    "Auto": "eng"
}

class TesseractOCREngine(BaseOCREngine):
    def extract_text(self, file_path: str, language: str = "English") -> Dict[str, Any]:
        lang_code = LANGUAGE_CODE_MAP.get(language, "eng")
        img = Image.open(file_path)
        
        ocr_text = pytesseract.image_to_string(img, lang=lang_code)
        
        try:
            data = pytesseract.image_to_data(img, lang=lang_code, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data.get('conf', []) if int(c) != -1]
            avg_conf = sum(confidences) / len(confidences) if confidences else 85.0
        except Exception:
            avg_conf = 85.0

        return {
            "text": ocr_text.strip(),
            "confidence": round(float(avg_conf), 1),
            "engine": f"Tesseract-OCR ({lang_code})"
        }
