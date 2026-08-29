from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    pending_review = db.query(Document).filter(
        (Document.status.in_(["Pending Review", "Low Confidence", "Owner Conflict", "Area Mismatch", "Duplicate"])) |
        (Document.processing_stage == "NEEDS_REVIEW")
    ).count()
    active_anomalies = db.query(ValidationResult).filter(ValidationResult.is_resolved == False).count()

    total_area_result = db.query(func.sum(LandRecord.area)).filter(LandRecord.verification_status == "Verified").scalar()
    total_area_digitized = round(float(total_area_result or 0.0), 2)

    # Status distribution
    status_counts = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
    status_dist = {s or "Pending Review": count for s, count in status_counts}
    for default_status in ["Verified", "Pending Review", "Low Confidence", "Owner Conflict", "Area Mismatch", "Duplicate"]:
        if default_status not in status_dist:
            status_dist[default_status] = 0

    # Document type distribution
    doc_types = db.query(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type).all()
    doc_type_dist = {dtype or "Other": count for dtype, count in doc_types}

    # Language distribution
    languages = db.query(Document.language, func.count(Document.id)).group_by(Document.language).all()
    lang_dist = {lang or "Unknown": count for lang, count in languages}

    # Recent activity
    recent_docs = db.query(Document).order_by(Document.created_at.desc()).limit(6).all()
    recent_records = db.query(LandRecord).order_by(LandRecord.updated_at.desc()).limit(6).all()

    return {
        "kpis": {
            "total_documents": total_docs,
            "digitized_records": verified_records,
            "pending_review": pending_review,
            "detected_anomalies": active_anomalies,
            "total_area_acres": total_area_digitized
        },
        "status_distribution": status_dist,
        "recent_activity": recent_docs,
        "document_type_distribution": doc_type_dist,
        "language_distribution": lang_dist,
        "recent_records": recent_records
    }
