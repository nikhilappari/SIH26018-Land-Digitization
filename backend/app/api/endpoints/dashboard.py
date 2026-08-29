from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.core.dependencies import get_db, get_current_active_user
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    total_docs = db.query(Document).count()
    verified_records = db.query(LandRecord).filter(LandRecord.verification_status == "Verified").count()
    pending_verifications = db.query(Document).filter(
        (Document.status.in_(["Pending Review", "Low Confidence", "Owner Conflict", "Area Mismatch", "Duplicate"])) |
        (Document.processing_stage == "NEEDS_REVIEW")
    ).count()

    total_area_result = db.query(func.sum(LandRecord.area)).filter(LandRecord.verification_status == "Verified").scalar()
    total_area_digitized = round(float(total_area_result or 0.0), 2)

    # Document type distribution
    doc_types = db.query(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type).all()
    doc_type_dist = {dtype or "Other": count for dtype, count in doc_types}

    # Language distribution
    languages = db.query(Document.language, func.count(Document.id)).group_by(Document.language).all()
    lang_dist = {lang or "Unknown": count for lang, count in languages}

    # Recent 5 documents
    recent_docs = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    
    # Recent 5 records
    recent_records = db.query(LandRecord).order_by(LandRecord.updated_at.desc()).limit(5).all()

    return {
        "total_documents_processed": total_docs,
        "verified_records_count": verified_records,
        "pending_human_review_count": pending_verifications,
        "total_area_digitized_acres": total_area_digitized,
        "document_type_distribution": doc_type_dist,
        "language_distribution": lang_dist,
        "recent_documents": recent_docs,
        "recent_records": recent_records
    }
