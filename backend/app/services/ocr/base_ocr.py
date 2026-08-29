from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseOCREngine(ABC):
    @abstractmethod
    def extract_text(self, file_path: str, language: str = "English") -> Dict[str, Any]:
        """
        Executes OCR on the given file path and returns:
        {
            "text": str,
            "confidence": float,
            "engine": str
        }
        """
        pass
