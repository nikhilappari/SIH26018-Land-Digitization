import datetime
import json
import logging
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

def log_verification_action(
    db: Session,
    document_id: int,
    user_id: int,
    action: str,
    previous_values: dict = None,
    new_values: dict = None,
    comments: str = ""
) -> AuditLog:
    """
    Creates an immutable audit log entry for human verification reviews.
    """
    try:
        prev_json = json.dumps(previous_values or {}, default=str)
        new_json = json.dumps(new_values or {}, default=str)
        
        audit_entry = AuditLog(
            document_id=document_id,
            user_id=user_id,
            action=action,
            previous_values=prev_json,
            new_values=new_json,
            comments=comments,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as e:
        logger.error(f"Audit log writing failed for document #{document_id}: {e}")
        return None
