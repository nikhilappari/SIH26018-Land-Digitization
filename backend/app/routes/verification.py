from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.land_records import LandRecord
from app.models.documents import Document
from app.models.audit import AuditLog
from app.models.validation import ValidationResult
from app.schemas.land_records import LandRecordResponse, LandRecordUpdate
from app.dependencies import get_current_active_user
from app.models.users import User

router = APIRouter(prefix="/verification", tags=["Human-in-the-Loop Verification"])

@router.get("/list")
def get_pending_verifications(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """Retrieve all documents that require human review."""
    pending_docs = db.query(Document).filter(
        Document.status.in_(["Pending Review", "Low Confidence", "Duplicate", "Area Mismatch", "Owner Conflict"])
    ).order_by(Document.created_at.desc()).all()
    
    res = []
    for doc in pending_docs:
        record = db.query(LandRecord).filter(LandRecord.document_id == doc.id).first()
        anomalies = db.query(ValidationResult).filter(ValidationResult.document_id == doc.id).all()
        res.append({
            "document_id": doc.id,
            "original_filename": doc.original_filename,
            "status": doc.status,
            "confidence_score": doc.confidence_score,
            "created_at": doc.created_at,
            "land_record": record,
            "anomalies_count": len(anomalies)
        })
    return res


@router.put("/{document_id}/verify")
def verify_document_record(
    document_id: int,
    record_update: LandRecordUpdate,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve/Reject land record, update database, and write audit log for modified fields.
    """
    # 1. Fetch document and associated land record
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    record = db.query(LandRecord).filter(LandRecord.document_id == document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Staged land record not found for this document")

    # 2. Check if already verified
    if record.verification_status == "Verified" and doc.status == "Verified":
        # We allow re-editing verified records, but log audit changes anyway
        pass

    # 3. Compile changed fields and create AuditLog entries
    update_data = record_update.dict(exclude_unset=True)
    
    audit_entries = []
    for field, new_val in update_data.items():
        if field in ["confidence_scores", "verification_status"]:
            continue
            
        old_val = getattr(record, field)
        
        # Standardize representation for comparison
        old_str = str(old_val).strip() if old_val is not None else ""
        new_str = str(new_val).strip() if new_val is not None else ""
        
        if old_str != new_str:
            audit_log = AuditLog(
                land_record_id=record.id,
                changed_by_user_id=current_user.id,
                field_name=field.replace('_', ' ').title(),
                old_value=old_str if old_val is not None else "None",
                new_value=new_str if new_val is not None else "None"
            )
            audit_entries.append(audit_log)
            # Update field on record
            setattr(record, field, new_val)

    # 4. Update status fields
    if approved:
        record.verification_status = "Verified"
        doc.status = "Verified"
        # Resolve all validation warnings
        db.query(ValidationResult).filter(ValidationResult.document_id == document_id).update({"is_resolved": True})
    else:
        record.verification_status = "Rejected"
        doc.status = "Error" # Mark as rejected

    # Save audit logs
    for entry in audit_entries:
        db.add(entry)

    db.commit()
    db.refresh(record)
    
    return {
        "message": "Land record verification completed successfully.",
        "record": record,
        "audits_logged": len(audit_entries)
    }


@router.get("/{record_id}/audits")
def get_record_audit_history(
    record_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """Retrieve audit history of a specific land record."""
    audits = db.query(AuditLog).filter(AuditLog.land_record_id == record_id).order_by(AuditLog.timestamp.desc()).all()
    
    res = []
    for a in audits:
        user = db.query(User).filter(User.id == a.changed_by_user_id).first() if a.changed_by_user_id else None
        res.append({
            "id": a.id,
            "field_name": a.field_name,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "timestamp": a.timestamp,
            "user_username": user.username if user else "System"
        })
    return res
