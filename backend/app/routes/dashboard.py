from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.documents import Document
from app.models.validation import ValidationResult
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Metrics"])

@router.get("/stats")
def get_dashboard_statistics(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Returns high-level statistics for the dashboard UI.
    """
    # 1. Total processed documents
    total_docs = db.query(Document).count()

    # 2. Digitized & Verified records
    verified_docs = db.query(Document).filter(Document.status == "Verified").count()

    # 3. Documents requiring review (any pending/low conf/anomalous status)
    review_statuses = ["Pending Review", "Low Confidence", "Duplicate", "Area Mismatch", "Owner Conflict"]
    needs_review = db.query(Document).filter(Document.status.in_(review_statuses)).count()

    # 4. Count of unresolved validation anomalies
    unresolved_anomalies = db.query(ValidationResult).filter(ValidationResult.is_resolved == False).count()

    # 5. Status distribution breakdown
    status_counts = db.query(Document.status, func.count(Document.status)).group_by(Document.status).all()
    status_distribution = {status: count for status, count in status_counts}

    # Fill default statuses if missing
    all_statuses = ["Processing", "Verified", "Pending Review", "Low Confidence", "Duplicate", "Area Mismatch", "Owner Conflict", "Error"]
    for s in all_statuses:
        if s not in status_distribution:
            status_distribution[s] = 0

    # 6. Recent Uploads & activities
    recent_uploads = db.query(Document).order_by(Document.created_at.desc()).limit(6).all()
    recent_activity = []
    for doc in recent_uploads:
        recent_activity.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status,
            "confidence_score": doc.confidence_score,
            "created_at": doc.created_at
        })

    return {
        "kpis": {
            "total_documents": total_docs,
            "digitized_records": verified_docs,
            "pending_review": needs_review,
            "detected_anomalies": unresolved_anomalies
        },
        "status_distribution": status_distribution,
        "recent_activity": recent_activity
    }
