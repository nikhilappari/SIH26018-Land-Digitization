import os
from typing import Optional
from app.services.preprocessing.image_cleaner import preprocess_image, detect_skew, rotate_image, denoise_photocopy
from app.services.preprocessing.pdf_processor import extract_pdf_pages_or_text

def clean_and_deskew_image(input_path: str, output_path: Optional[str] = None) -> str:
    if output_path is None:
        os.makedirs("preprocessed", exist_ok=True)
        base_name = os.path.basename(input_path)
        output_path = os.path.join("preprocessed", f"clean_{base_name}")
    preprocess_image(input_path, output_path)
    return output_path

process_pdf_document = extract_pdf_pages_or_text

__all__ = [
    "preprocess_image",
    "clean_and_deskew_image",
    "detect_skew",
    "rotate_image",
    "denoise_photocopy",
    "extract_pdf_pages_or_text",
    "process_pdf_document"
]
