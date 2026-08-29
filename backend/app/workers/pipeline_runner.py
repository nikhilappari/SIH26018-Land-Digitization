import os
import logging
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
from app.services.preprocessing import clean_and_deskew_image, process_pdf_document
from app.services.language import detect_language, classify_document_type
from app.services.ocr import TesseractOCREngine, OnlineOCREngine
from app.services.extraction import MultilingualFieldExtractor
from app.services.validation import validate_record
from app.services.confidence import calculate_document_confidence

logger = logging.getLogger(__name__)

def run_document_digitization_pipeline(document_id: int):
    """
    Asynchronous end-to-end digitization pipeline with structured bounding boxes,
    multilingual extraction, normalization, and statutory revenue validation.
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Pipeline error: Document #{document_id} not found in database.")
            return

        logger.info(f"==> Starting Land Record Digitization Pipeline for Document #{doc.id}: {doc.original_filename}")

        # -------------------------------------------------------------
        # Stage 1: PREPROCESSING (Noise removal, Deskew, Contrast)
        # -------------------------------------------------------------
        doc.processing_stage = "PREPROCESSING"
        doc.status = "Processing"
        db.commit()

        ext = os.path.splitext(doc.file_path)[1].lower()
        preprocessed_path = doc.file_path
        
        if ext == '.pdf':
            pdf_result = process_pdf_document(doc.file_path)
            preprocessed_path = pdf_result.get("rendered_images", [doc.file_path])[0]
        elif ext in ['.jpg', '.jpeg', '.png']:
            preprocessed_path = clean_and_deskew_image(doc.file_path)

        doc.preprocessed_path = preprocessed_path
        db.commit()
        logger.info(f"Stage 1 Completed: Preprocessed image generated at {preprocessed_path}")

        # -------------------------------------------------------------
        # Stage 2: OCR EXECUTION (Multi-Engine with Bounding Box Overlay)
        # -------------------------------------------------------------
        doc.processing_stage = "OCR_PROCESSING"
        db.commit()

        # Step 2a: Run OCR Engine
        online_ocr = OnlineOCREngine()
        ocr_result = online_ocr.extract_text(preprocessed_path, language="auto")
        
        if not ocr_result.get("text") or len(ocr_result["text"].strip()) < 15:
            logger.info("Online OCR returned minimal text. Falling back to local Multilingual Tesseract...")
            tesseract_ocr = TesseractOCREngine()
            ocr_result = tesseract_ocr.extract_text(preprocessed_path, language=doc.language or "English")

        raw_ocr_text = ocr_result.get("text", "")
        ocr_conf = float(ocr_result.get("confidence", 80.0))
        doc.ocr_text = raw_ocr_text
        logger.info(f"Stage 2 Completed: OCR produced {len(raw_ocr_text)} characters (Conf: {ocr_conf}%)")

        # -------------------------------------------------------------
        # Stage 3: LANGUAGE DETECTION & DOCUMENT CLASSIFICATION
        # -------------------------------------------------------------
        doc.processing_stage = "CLASSIFYING"
        db.commit()

        detected_lang = detect_language(raw_ocr_text)
        detected_doc_type = classify_document_type(raw_ocr_text, doc.original_filename)

        doc.language = detected_lang
        doc.doc_type = detected_doc_type
        db.commit()
        logger.info(f"Stage 3 Completed: Detected Language='{detected_lang}', Doc Type='{detected_doc_type}'")

        # -------------------------------------------------------------
        # Stage 4: MULTILINGUAL FIELD EXTRACTION & NORMALIZATION
        # -------------------------------------------------------------
        doc.processing_stage = "EXTRACTING"
        db.commit()

        extractor = MultilingualFieldExtractor()
        structured_fields, staging_data = extractor.extract_all(ocr_result, ocr_conf)
        confidences = {k: v["confidence"] for k, v in structured_fields.items()}
        logger.info(f"Stage 4 Completed: Extracted fields: {staging_data}")

        # -------------------------------------------------------------
        # Stage 5: VALIDATION & ANOMALY DETECTION
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
        # Stage 6: STAGING LAND RECORD & CONFIDENCE SCORING
        # -------------------------------------------------------------
        overall_confidence = calculate_document_confidence(confidences, ocr_conf, len(anomalies))
        doc.confidence_score = overall_confidence

        # Determine Final Status
        if len(anomalies) > 0:
            doc.status = "Pending Review"
            doc.processing_stage = "NEEDS_REVIEW"
        elif overall_confidence < 75.0:
            doc.status = "Low Confidence"
            doc.processing_stage = "NEEDS_REVIEW"
        else:
            doc.status = "Verified"
            doc.processing_stage = "COMPLETED"

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
