from pydantic import BaseModel
from datetime import datetime

class ValidationResultResponse(BaseModel):
    id: int
    document_id: int
    rule_name: str
    severity: str
    description: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
