import os
import requests
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.ocr.base_ocr import BaseOCREngine

logger = logging.getLogger(__name__)

class OnlineOCREngine(BaseOCREngine):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OCR_SPACE_API_KEY or "helloworld"
        self.url = "https://api.ocr.space/parse/image"

    def extract_text(self, file_path: str, language: str = "auto") -> Dict[str, Any]:
        """
        Sends image to OCR.space Engine 2 (multilingual Indic support).
        """
        try:
            logger.info(f"Connecting to OCR.space online engine for {os.path.basename(file_path)}...")
            with open(file_path, 'rb') as f:
                response = requests.post(
                    self.url,
                    files={'file': f},
                    data={
                        'apikey': self.api_key,
                        'language': 'auto',
                        'OCREngine': '2',
                        'scale': True,
                        'isTable': True
                    },
                    timeout=25
                )
            result = response.json()
            if result.get("OCRExitCode") == 1:
                parsed_results = result.get("ParsedResults", [])
                if parsed_results:
                    text = parsed_results[0].get("ParsedText", "").strip()
                    logger.info("Online OCR extracted text successfully.")
                    return {
                        "text": text,
                        "confidence": 88.0,
                        "engine": "OCR.space Online API (Engine 2)"
                    }
            logger.warning(f"OCR.space API message: {result.get('ErrorMessage')}")
        except Exception as e:
            logger.warning(f"Online OCR request failed: {str(e)}")
            
        return {
            "text": "",
            "confidence": 0.0,
            "engine": "Failed"
        }
