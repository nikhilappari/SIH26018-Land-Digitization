from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_path: str
    preprocessed_path: Optional[str] = None
    doc_type: str
    language: str
    format_type: str
    status: str
    confidence_score: float
    processing_stage: Optional[str] = "UPLOADED"
    ocr_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    doc_type: Optional[str] = None
    language: Optional[str] = None
    format_type: Optional[str] = None
    status: Optional[str] = None
    confidence_score: Optional[float] = None
