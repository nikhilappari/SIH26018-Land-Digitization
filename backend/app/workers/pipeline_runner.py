import os
import logging
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
from app.services.preprocessing import preprocess_image
from app.services.language import classify_document
from app.services.ocr import run_ocr
from app.services.normalization import translate_to_english
from app.services.extraction import extract_fields
from app.services.validation import validate_record
from app.services.confidence import calculate_field_confidences, calculate_overall_confidence
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_document_digitization_pipeline(document_id: int):
    """
    Asynchronous digitization pipeline coordinator:
    UPLOADED -> PREPROCESSING -> CLASSIFYING -> OCR_PROCESSING -> EXTRACTING -> VALIDATING -> COMPLETED / NEEDS_REVIEW
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"[PIPELINE ERROR] Document ID {document_id} not found in database.")
            return

        logger.info(f"[PIPELINE START] Processing document ID {document_id} ({doc.original_filename})")

        # 1. Preprocessing Stage
        doc.processing_stage = "PREPROCESSING"
        db.commit()
        
        preprocessed_filename = f"preprocessed_{os.path.basename(doc.file_path)}"
        preprocessed_full_path = os.path.join(settings.PREPROCESSED_DIR, preprocessed_filename)
        
        prep_res = preprocess_image(doc.file_path, preprocessed_full_path)
        if prep_res.get("success", False):
            doc.preprocessed_path = f"/static/preprocessed/{preprocessed_filename}"
            db.commit()
        else:
            logger.warning(f"Image preprocessing returned error: {prep_res.get('error')}")

        # 2. Classification & Language Detection Stage
        doc.processing_stage = "CLASSIFYING"
        db.commit()
        
        # Initial classification from filename
        classification = classify_document("", doc.original_filename)
        doc.doc_type = classification.get("doc_type", "Other")
        target_language = doc.language if doc.language and doc.language != "Auto" else classification.get("language", "English")
        doc.language = target_language
        doc.format_type = classification.get("format_type", "Printed")
        db.commit()

        # 3. OCR Stage
        doc.processing_stage = "OCR_PROCESSING"
        db.commit()
        
        ocr_source_image = preprocessed_full_path if os.path.exists(preprocessed_full_path) else doc.file_path
        ocr_result = run_ocr(ocr_source_image, target_language)
        
        ocr_text = ocr_result.get("text", "")
        ocr_confidence = ocr_result.get("confidence", 85.0)
        
        # Re-classify with actual OCR text
        if ocr_text:
            text_classification = classify_document(ocr_text, doc.original_filename)
            if text_classification.get("doc_type") != "Other":
                doc.doc_type = text_classification.get("doc_type")
            if not doc.language or doc.language == "Auto" or doc.language == "English":
                doc.language = text_classification.get("language", "English")

        doc.ocr_text = ocr_text
        doc.confidence_score = ocr_confidence
        db.commit()

        # 4. Multilingual Translation & Normalization (if non-English)
        parsed_text = ocr_text
        if doc.language != "English" and ocr_text:
            parsed_text = translate_to_english(ocr_text, doc.language)

        # 5. Extraction Stage
        doc.processing_stage = "EXTRACTING"
        db.commit()
        
        fields, raw_confidences = extract_fields(parsed_text, ocr_confidence)
        confidences = calculate_field_confidences(fields, ocr_confidence)
        overall_conf = calculate_overall_confidence(confidences)
        
        doc.confidence_score = overall_conf

        # 6. Validation Stage
        doc.processing_stage = "VALIDATING"
        db.commit()
        
        validation_anomalies = validate_record(db, fields, document_id)

        # 7. Persist Land Record & Validation Results
        land_rec = db.query(LandRecord).filter(LandRecord.document_id == document_id).first()
        if not land_rec:
            land_rec = LandRecord(
                document_id=document_id,
                owner_name=fields.get("owner_name"),
                survey_number=fields.get("survey_number"),
                khasra_number=fields.get("khasra_number"),
                khata_number=fields.get("khata_number"),
                plot_number=fields.get("plot_number"),
                area=fields.get("area"),
                area_unit=fields.get("area_unit", "Acres"),
                village=fields.get("village"),
                tehsil_mandal=fields.get("tehsil_mandal"),
                district=fields.get("district"),
                land_classification=fields.get("land_classification"),
                ownership_type=fields.get("ownership_type"),
                mutation_number=fields.get("mutation_number"),
                registration_number=fields.get("registration_number"),
                registration_date=fields.get("registration_date"),
                confidence_scores=confidences,
                verification_status="Pending",
                regional_values={}
            )
            db.add(land_rec)
        else:
            for k, v in fields.items():
                if hasattr(land_rec, k):
                    setattr(land_rec, k, v)
            land_rec.confidence_scores = confidences

        # Clear older validations if re-running
        db.query(ValidationResult).filter(ValidationResult.document_id == document_id).delete()

        has_errors = False
        has_warnings = False

        for anomaly in validation_anomalies:
            severity = anomaly.get("severity", "Warning")
            if severity == "Error":
                has_errors = True
            elif severity == "Warning":
                has_warnings = True

            vr = ValidationResult(
                document_id=document_id,
                rule_name=anomaly.get("rule_name", "General Check"),
                severity=severity,
                description=anomaly.get("description", "")
            )
            db.add(vr)

        # 8. Status & Stage Resolution
        if has_errors:
            rule_names = [a.get("rule_name") for a in validation_anomalies if a.get("severity") == "Error"]
            if "Owner Conflict" in rule_names:
                doc.status = "Owner Conflict"
            elif "Area Mismatch" in rule_names:
                doc.status = "Area Mismatch"
            else:
                doc.status = "Low Confidence"
            doc.processing_stage = "NEEDS_REVIEW"
        elif overall_conf < 80.0:
            doc.status = "Low Confidence"
            doc.processing_stage = "NEEDS_REVIEW"
        elif has_warnings:
            rule_names = [a.get("rule_name") for a in validation_anomalies if a.get("severity") == "Warning"]
            if "Duplicate" in rule_names:
                doc.status = "Duplicate"
            else:
                doc.status = "Pending Review"
            doc.processing_stage = "NEEDS_REVIEW"
        else:
            doc.status = "Verified"
            doc.processing_stage = "COMPLETED"
            land_rec.verification_status = "Verified"

        db.commit()
        logger.info(f"[PIPELINE COMPLETED] Document ID {document_id} resolved with status '{doc.status}' at stage '{doc.processing_stage}'.")

    except Exception as e:
        db.rollback()
        logger.exception(f"[PIPELINE FATAL ERROR] Exception processing document ID {document_id}: {str(e)}")
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "Error"
                doc.processing_stage = "FAILED"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
