from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class LandRecordBase(BaseModel):
    owner_name: Optional[str] = None
    survey_number: Optional[str] = None
    khasra_number: Optional[str] = None
    khata_number: Optional[str] = None
    plot_number: Optional[str] = None
    area: Optional[float] = None
    area_unit: Optional[str] = "Acres"
    village: Optional[str] = None
    tehsil_mandal: Optional[str] = None
    district: Optional[str] = None
    land_classification: Optional[str] = None
    ownership_type: Optional[str] = None
    mutation_number: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    regional_values: Optional[Dict[str, Any]] = None

class LandRecordCreate(LandRecordBase):
    document_id: Optional[int] = None
    confidence_scores: Optional[Dict[str, float]] = None
    verification_status: Optional[str] = "Pending"

class LandRecordUpdate(LandRecordBase):
    confidence_scores: Optional[Dict[str, float]] = None
    verification_status: Optional[str] = None

class LandRecordResponse(LandRecordBase):
    id: int
    document_id: Optional[int]
    confidence_scores: Optional[Dict[str, Any]] = None
    verification_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
