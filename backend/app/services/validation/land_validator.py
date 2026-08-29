from sqlalchemy.orm import Session
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
import re
from typing import List, Dict, Any

def validate_record(db: Session, record_data: Dict[str, Any], document_id: int) -> List[Dict[str, Any]]:
    """
    Validates a land record against standard governance rules and existing database records.
    Returns a list of anomaly dictionaries:
    [
        {"rule_name": str, "severity": str, "description": str}
    ]
    """
    anomalies = []
    
    owner_name = record_data.get("owner_name")
    survey_number = record_data.get("survey_number")
    area = record_data.get("area")
    area_unit = record_data.get("area_unit", "Acres")
    village = record_data.get("village")
    tehsil_mandal = record_data.get("tehsil_mandal")
    district = record_data.get("district")
    reg_date = record_data.get("registration_date")
    khata_number = record_data.get("khata_number")
    doc_type = record_data.get("doc_type", "Other")

    # 1. Format and Missing Field Checks
    required_fields = {
        "owner_name": "Owner Name",
        "survey_number": "Survey Number",
        "area": "Area/Extent",
        "village": "Village",
        "tehsil_mandal": "Tehsil/Mandal",
        "district": "District"
    }

    for field, label in required_fields.items():
        if not record_data.get(field):
            if doc_type == "Mutation Record" and field == "owner_name":
                continue
            anomalies.append({
                "rule_name": "Missing Field",
                "severity": "Warning",
                "description": f"Required field '{label}' is missing from the record."
            })

    # Validate Area format
    if area is not None:
        try:
            val = float(area)
            if val <= 0:
                anomalies.append({
                    "rule_name": "Format Error",
                    "severity": "Error",
                    "description": f"Invalid Area value ({area}). Area must be a positive number."
                })
        except ValueError:
            anomalies.append({
                "rule_name": "Format Error",
                "severity": "Error",
                "description": f"Invalid Area format ({area}). Must be a decimal number."
            })

    # Validate Registration Date format (DD-MM-YYYY or YYYY-MM-DD)
    if reg_date:
        date_pattern = r'^\d{2}-\d{2}-\d{4}$'
        if not re.match(date_pattern, str(reg_date)):
            anomalies.append({
                "rule_name": "Format Error",
                "severity": "Warning",
                "description": f"Date '{reg_date}' does not match standard DD-MM-YYYY format."
            })

    # 2. Cross-Document / Database Check (duplicate, area mismatch, owner conflict)
    if survey_number and village and tehsil_mandal:
        query = db.query(LandRecord).filter(
            LandRecord.survey_number == survey_number,
            LandRecord.village == village,
            LandRecord.tehsil_mandal == tehsil_mandal,
            LandRecord.verification_status == "Verified"
        )
        
        if document_id:
            query = query.filter(LandRecord.document_id != document_id)
            
        existing_records = query.all()
        
        for existing in existing_records:
            # Duplicate check
            if (owner_name == existing.owner_name and 
                abs((area or 0.0) - (existing.area or 0.0)) < 0.01 and 
                khata_number == existing.khata_number):
                anomalies.append({
                    "rule_name": "Duplicate",
                    "severity": "Warning",
                    "description": f"Possible duplicate: An identical verified record already exists in database (Record ID: {existing.id})."
                })
                continue

            # Owner Conflict check
            if (doc_type != "Mutation Record" and 
                owner_name and existing.owner_name and 
                owner_name.strip().lower() != existing.owner_name.strip().lower()):
                anomalies.append({
                    "rule_name": "Owner Conflict",
                    "severity": "Error",
                    "description": f"Owner mismatch! Survey #{survey_number} is registered to '{existing.owner_name}' in DB (Record ID: {existing.id}), but document says '{owner_name}'."
                })

            # Area Mismatch check
            if area is not None and existing.area is not None:
                area_diff = abs(float(area) - float(existing.area))
                if area_diff > 0.05:
                    anomalies.append({
                        "rule_name": "Area Mismatch",
                        "severity": "Error",
                        "description": f"Area discrepancy detected! Extent is {area} {area_unit}, but existing record has {existing.area} {existing.area_unit} (difference of {round(area_diff, 2)} {area_unit})."
                    })

    return anomalies
