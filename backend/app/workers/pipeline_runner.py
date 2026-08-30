import os
import logging
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
from app.services.preprocessing import clean_and_deskew_image, extract_pdf_pages_or_text
from app.services.ocr import run_ocr
from app.services.handwriting import assess_handwriting_and_quality
from app.services.language_detection import detect_language
from app.services.document_classification import classify_document_type
from app.services.field_extraction import MultilingualFieldExtractor, AILandExtractionAgent
from app.services.validation import validate_record
from app.services.confidence import calculate_document_confidence
from app.services.verification import evaluate_verification_routing

logger = logging.getLogger(__name__)

def run_document_digitization_pipeline(document_id: int):
    """
    Asynchronous end-to-end modular AI land digitization pipeline:
    1. Preprocessing (PyMuPDF rendering + Skew/Noise/CLAHE enhancement)
    2. Multi-Engine OCR with spatial bounding box extraction
    3. Language Detection & Document Classification
    4. Handwriting & Image Quality Assessment
    5. Multilingual Field Extraction & Provenance Tracking
    6. Canonical Normalization (Dates, Extents, Place Names)
    7. Statutory Revenue Validation & Anomaly Detection
    8. Confidence Scoring & Verification Routing
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Pipeline error: Document #{document_id} not found in database.")
            return

        logger.info(f"==> Starting Land Record Digitization Pipeline for Document #{doc.id}: {doc.original_filename}")

        # -------------------------------------------------------------
        # Stage 1: PREPROCESSING (Multi-page PDF / High-res OpenCV Enhancement)
        # -------------------------------------------------------------
        doc.processing_stage = "PREPROCESSING"
        doc.status = "Processing"
        db.commit()

        ext = os.path.splitext(doc.file_path)[1].lower()
        preprocessed_path = doc.file_path
        
        if ext == '.pdf':
            pdf_result = extract_pdf_pages_or_text(doc.file_path)
            preprocessed_path = pdf_result.get("rendered_images", [doc.file_path])[0]
        elif ext in ['.jpg', '.jpeg', '.png']:
            preprocessed_path = clean_and_deskew_image(doc.file_path)

        doc.preprocessed_path = preprocessed_path
        db.commit()
        logger.info(f"Stage 1 Completed: Preprocessed image generated at {preprocessed_path}")

        # -------------------------------------------------------------
        # Stage 2: MULTI-ENGINE OCR (RapidOCR Neural -> Fallback)
        # -------------------------------------------------------------
        doc.processing_stage = "OCR_PROCESSING"
        db.commit()

        # Primary pass on original image, fallback to preprocessed
        ocr_result = run_ocr(doc.file_path, language=doc.language or "English")
        if not ocr_result.get("text") or len(ocr_result["text"].strip()) < 30:
            if preprocessed_path and os.path.exists(preprocessed_path) and preprocessed_path != doc.file_path:
                ocr_prep = run_ocr(preprocessed_path, language=doc.language or "English")
                if len(ocr_prep.get("text", "")) > len(ocr_result.get("text", "")):
                    ocr_result = ocr_prep

        raw_ocr_text = ocr_result.get("text", "")
        ocr_conf = float(ocr_result.get("confidence", 85.0))
        doc.ocr_text = raw_ocr_text
        logger.info(f"Stage 2 Completed: OCR produced {len(raw_ocr_text)} characters via {ocr_result.get('engine', 'OCR')} (Conf: {ocr_conf}%)")

        # -------------------------------------------------------------
        # Stage 3: LANGUAGE DETECTION, CLASSIFICATION & HTR ASSESSMENT
        # -------------------------------------------------------------
        doc.processing_stage = "CLASSIFYING"
        db.commit()

        classification = classify_document_type(raw_ocr_text, doc.original_filename)
        htr_info = assess_handwriting_and_quality(doc.file_path, ocr_result.get("lines", []))

        detected_lang = classification.get("language") or detect_language(raw_ocr_text, doc.original_filename)
        doc_type_str = classification.get("doc_type", "Other")
        format_type_str = htr_info.get("format_type", "Printed")

        doc.language = detected_lang
        doc.doc_type = doc_type_str
        doc.format_type = format_type_str
        db.commit()
        logger.info(f"Stage 3 Completed: Language='{detected_lang}', Doc Type='{doc_type_str}', Format='{format_type_str}'")

        # -------------------------------------------------------------
        # Stage 4: MULTILINGUAL FIELD EXTRACTION & AI AGENT ENSEMBLE
        # -------------------------------------------------------------
        doc.processing_stage = "EXTRACTING"
        db.commit()

        agent = AILandExtractionAgent()
        structured_fields, staging_data = agent.extract_with_ensemble(
            ocr_result=ocr_result,
            doc_confidence=ocr_conf,
            language=doc.language or "English",
            doc_type=doc.doc_type or "Other"
        )
        confidences = {k: v["confidence"] for k, v in structured_fields.items()}
        logger.info(f"Stage 4 Completed: Extracted fields: {staging_data}")

        # -------------------------------------------------------------
        # Stage 5: STATUTORY REVENUE VALIDATION & ANOMALIES
        # -------------------------------------------------------------
        doc.processing_stage = "VALIDATING"
        db.commit()

        # Clear prior validation results if any
        db.query(ValidationResult).filter(ValidationResult.document_id == doc.id).delete()
        
        anomalies = validate_record(db, staging_data, doc.id)
        for a in anomalies:
            new_anom = ValidationResult(
                document_id=doc.id,
                rule_name=a["rule_name"],
                severity=a["severity"],
                description=a["description"],
                is_resolved=False
            )
            db.add(new_anom)
        db.commit()

        # -------------------------------------------------------------
        # Stage 6: CONFIDENCE SCORING & VERIFICATION ROUTING
        # -------------------------------------------------------------
        overall_confidence = calculate_document_confidence(confidences, ocr_conf, len(anomalies))
        doc.confidence_score = overall_confidence

        routing = evaluate_verification_routing(
            overall_confidence=overall_confidence,
            anomalies=anomalies,
            is_handwritten=(format_type_str == "Handwritten")
        )

        doc.status = routing["status"]
        doc.processing_stage = routing["processing_stage"]

        # Create or Update LandRecord staging entry
        existing_record = db.query(LandRecord).filter(LandRecord.document_id == doc.id).first()
        if not existing_record:
            land_record = LandRecord(
                document_id=doc.id,
                owner_name=staging_data.get("owner_name"),
                survey_number=staging_data.get("survey_number"),
                khasra_number=staging_data.get("khasra_number"),
                khata_number=staging_data.get("khata_number"),
                plot_number=staging_data.get("plot_number"),
                area=staging_data.get("area"),
                area_unit=staging_data.get("area_unit", "Acres"),
                village=staging_data.get("village"),
                tehsil_mandal=staging_data.get("tehsil_mandal"),
                district=staging_data.get("district"),
                land_classification=staging_data.get("land_classification"),
                registration_number=staging_data.get("registration_number"),
                registration_date=staging_data.get("registration_date"),
                confidence_scores=confidences,
                regional_values=structured_fields,
                verification_status="Verified" if doc.status == "Verified" else "Pending"
            )
            db.add(land_record)
        else:
            for k, v in staging_data.items():
                if hasattr(existing_record, k):
                    setattr(existing_record, k, v)
            existing_record.confidence_scores = confidences
            existing_record.regional_values = structured_fields
            existing_record.verification_status = "Verified" if doc.status == "Verified" else "Pending"

        db.commit()
        db.refresh(doc)
        logger.info(f"==> Digitization Pipeline for Document #{doc.id} Completed with Status='{doc.status}' (Conf: {overall_confidence}%)")

    except Exception as e:
        logger.exception(f"Unhandled error during digitization pipeline: {str(e)}")
        if doc:
            doc.status = "Error"
            doc.processing_stage = "FAILED"
            db.commit()
    finally:
        db.close()
