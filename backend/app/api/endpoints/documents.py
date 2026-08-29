import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.config import settings
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
from app.schemas.documents import DocumentResponse, DocumentDetailResponse
from app.workers.pipeline_runner import run_document_digitization_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("Auto"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload JPG, PNG, or PDF files."
        )

    # Save original file securely with UUID
    unique_fn = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_fn)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    new_doc = Document(
        original_filename=file.filename,
        file_path=file_path,
        status="Processing",
        language=language,
        confidence_score=0.0,
        processing_stage="UPLOADED"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Trigger background digitization pipeline
    background_tasks.add_task(run_document_digitization_pipeline, new_doc.id)

    return new_doc

@router.get("", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{document_id}/extraction-debug")
def get_extraction_debug(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    land_record = db.query(LandRecord).filter(LandRecord.document_id == document_id).first()
    validations = db.query(ValidationResult).filter(ValidationResult.document_id == document_id).all()

    return {
        "document_id": doc.id,
        "filename": doc.original_filename,
        "raw_ocr": doc.ocr_text,
        "language": doc.language,
        "doc_type": doc.doc_type,
        "processing_stage": doc.processing_stage,
        "overall_confidence": doc.confidence_score,
        "fields": land_record.regional_values if land_record else None,
        "staging_record": {
            "owner_name": land_record.owner_name if land_record else None,
            "survey_number": land_record.survey_number if land_record else None,
            "khata_number": land_record.khata_number if land_record else None,
            "khasra_number": land_record.khasra_number if land_record else None,
            "area": land_record.area if land_record else None,
            "area_unit": land_record.area_unit if land_record else None,
            "village": land_record.village if land_record else None,
            "tehsil_mandal": land_record.tehsil_mandal if land_record else None,
            "district": land_record.district if land_record else None,
            "registration_number": land_record.registration_number if land_record else None,
            "registration_date": land_record.registration_date if land_record else None
        } if land_record else None,
        "validation": [
            {
                "rule_name": v.rule_name,
                "severity": v.severity,
                "description": v.description,
                "is_resolved": v.is_resolved
            }
            for v in validations
        ]
    }

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(
    document_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    land_record = db.query(LandRecord).filter(LandRecord.document_id == document_id).first()
    validations = db.query(ValidationResult).filter(ValidationResult.document_id == document_id).all()
    
    return {
        "document": doc,
        "land_record": land_record,
        "validation_results": validations
    }
