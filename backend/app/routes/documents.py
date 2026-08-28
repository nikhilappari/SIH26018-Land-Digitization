import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Form
from sqlalchemy.orm import Session
import shutil
import uuid
import logging

from app.database import get_db, SessionLocal
from app.models.documents import Document
from app.models.land_records import LandRecord
from app.models.validation import ValidationResult
from app.schemas.documents import DocumentResponse
from app.dependencies import get_current_active_user
from app.config import settings

# Service Imports
from app.services.preprocessing import preprocess_image
from app.services.ocr import run_ocr
from app.services.classification import classify_document
from app.services.nlp_extractor import extract_fields
from app.services.validation import validate_record
from app.services.translation import translate_to_english

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

def run_document_digitization_pipeline(document_id: int):
    """
    Background worker that runs the entire digitization & validation pipeline.
    """
    db = SessionLocal()
    try:
        # 1. Fetch document from db
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document ID {document_id} not found in database for background processing.")
            return

        logger.info(f"[START] Digitization pipeline started for document ID {document_id}: {doc.original_filename}")
        
        # Define preprocessed file path
        filename_only, ext = os.path.splitext(os.path.basename(doc.file_path))
        preprocessed_filename = f"preprocessed_{filename_only}.png"
        preprocessed_path = os.path.join(settings.PREPROCESSED_DIR, preprocessed_filename)
        doc.preprocessed_path = f"/static/preprocessed/{preprocessed_filename}"

        # 2. Image Preprocessing
        logger.info(f"[PREPROCESSING] Starting for document ID {document_id}")
        doc.processing_stage = "PREPROCESSING"
        db.commit()

        prep_results = preprocess_image(doc.file_path, preprocessed_path)
        if not prep_results.get("success", False):
            doc.status = "Error"
            doc.processing_stage = "FAILED"
            db.commit()
            logger.error(f"[PREPROCESSING] Failed for document ID {document_id}: {prep_results.get('error')}")
            return
        
        logger.info(f"[PREPROCESSING] Success for document ID {document_id}")

        # 3. Document Classification & OCR
        logger.info(f"[CLASSIFICATION] Starting for document ID {document_id}")
        doc.processing_stage = "CLASSIFYING"
        db.commit()

        # Resolve OCR language pack
        if doc.language and doc.language != "Auto":
            ocr_lang = doc.language
        else:
            ocr_lang = "English"  # Default
            # Let's run a quick heuristic language check on filename before running OCR
            fn_lower = doc.original_filename.lower()
            if "telugu" in fn_lower or "adangal" in fn_lower or "pahani" in fn_lower:
                ocr_lang = "Telugu"
            elif "hindi" in fn_lower or "khasra" in fn_lower:
                ocr_lang = "Hindi"

        logger.info(f"[OCR] Starting for document ID {document_id} with language '{ocr_lang}'")
        doc.processing_stage = "OCR_PROCESSING"
        db.commit()

        ocr_results = run_ocr(preprocessed_path, language=ocr_lang)
        doc.ocr_text = ocr_results["text"]
        ocr_confidence = ocr_results.get("confidence", 85.0)
        
        # Check if OCR returned empty text
        if not doc.ocr_text.strip():
            logger.warning(f"[OCR] Extracted empty/unreadable text for document ID {document_id}")
            doc.status = "Low Confidence"
            doc.processing_stage = "NEEDS_REVIEW"
            db.commit()
            return
            
        # Classify the document based on extracted text and filename
        classification = classify_document(doc.ocr_text, doc.original_filename)
        doc.doc_type = classification["doc_type"]
        if not doc.language or doc.language == "Auto":
            doc.language = classification["language"]
        doc.format_type = classification["format_type"]
        
        # 4. Information Extraction (NLP & Rules)
        logger.info(f"[EXTRACTION] Starting for document ID {document_id}")
        doc.processing_stage = "EXTRACTING"
        db.commit()

        # Translate to English if regional language, and capture regional values
        regional_values = {}
        if doc.language != "English":
            translated_text = translate_to_english(doc.ocr_text, doc.language)
            # Extract attributes in original script
            reg_fields, _, _ = extract_fields(doc.ocr_text, ocr_confidence)
            for k, v in reg_fields.items():
                if v is not None:
                    regional_values[k] = v
        else:
            translated_text = doc.ocr_text

        fields, confidences, overall_conf = extract_fields(translated_text, ocr_confidence)
        doc.confidence_score = overall_conf
        
        # Let's save a structured land record linking back to document
        land_rec = LandRecord(
            document_id=doc.id,
            owner_name=fields["owner_name"],
            survey_number=fields["survey_number"],
            khasra_number=fields["khasra_number"],
            khata_number=fields["khata_number"],
            plot_number=fields["plot_number"],
            area=fields["area"],
            area_unit=fields["area_unit"],
            village=fields["village"],
            tehsil_mandal=fields["tehsil_mandal"],
            district=fields["district"],
            land_classification=fields["land_classification"],
            ownership_type=fields["ownership_type"],
            mutation_number=fields["mutation_number"],
            registration_number=fields["registration_number"],
            registration_date=fields["registration_date"],
            confidence_scores=confidences,
            verification_status="Pending",
            regional_values=regional_values
        )
        db.add(land_rec)
        db.flush() # Gain access to land_rec.id

        # 5. Validation and Anomaly Detection
        logger.info(f"[VALIDATION] Starting for document ID {document_id}")
        doc.processing_stage = "VALIDATING"
        db.commit()

        # Pass doc_type into fields for context-aware validation
        fields["doc_type"] = doc.doc_type
        validation_results = validate_record(db, fields, doc.id)
        
        for vr in validation_results:
            db.add(vr)
            
        # Determine Routing Status
        has_errors = any(v.severity == "Error" for v in validation_results)
        has_warnings = any(v.severity == "Warning" for v in validation_results)
        
        # Set specific status flags based on validation errors
        if has_errors:
            # Detect primary error type for status badge mapping
            rule_names = [v.rule_name for v in validation_results if v.severity == "Error"]
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
            # e.g., Duplicate warning
            rule_names = [v.rule_name for v in validation_results if v.severity == "Warning"]
            if "Duplicate" in rule_names:
                doc.status = "Duplicate"
            else:
                doc.status = "Pending Review"
            doc.processing_stage = "NEEDS_REVIEW"
        else:
            # Auto-accept: high confidence, zero warnings/errors
            doc.status = "Verified"
            doc.processing_stage = "COMPLETED"
            land_rec.verification_status = "Verified"

        db.commit()
        logger.info(f"[DATABASE] Pipeline completed successfully for document ID {document_id}. Final status: {doc.status}")

    except Exception as e:
        db.rollback()
        logger.exception(f"[ERROR] Exception executing pipeline for document ID {document_id}: {str(e)}")
        # Update doc status to Error
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


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("Auto"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Ensure correct extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload JPG, PNG, or PDF files."
        )

    # Save original file
    unique_fn = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_fn)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Create Document record
    new_doc = Document(
        original_filename=file.filename,
        file_path=file_path,
        status="Processing",
        language=language,
        confidence_score=0.0,
        processing_stage="UPLOADED"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Start background execution
    background_tasks.add_task(run_document_digitization_pipeline, new_doc.id)

    # Format return urls (relative path for frontend static mount mapping)
    # We will overwrite path representations for serialization safety
    res = DocumentResponse(
        id=new_doc.id,
        original_filename=new_doc.original_filename,
        file_path=f"/static/uploads/{unique_fn}",
        preprocessed_path=None,
        doc_type=new_doc.doc_type,
        language=new_doc.language,
        format_type=new_doc.format_type,
        status=new_doc.status,
        confidence_score=new_doc.confidence_score,
        processing_stage=new_doc.processing_stage,
        ocr_text=None,
        created_at=new_doc.created_at
    )
    return res


@router.get("", response_model=list[DocumentResponse])
def get_documents_list(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    # Update paths to be web-friendly relative urls
    res = []
    for doc in docs:
        fn = os.path.basename(doc.file_path)
        doc_res = DocumentResponse.from_orm(doc)
        doc_res.file_path = f"/static/uploads/{fn}"
        res.append(doc_res)
    return res


@router.get("/{document_id}")
def get_document_details(
    document_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    fn = os.path.basename(doc.file_path)
    file_url = f"/static/uploads/{fn}"
    
    # Retrieve the associated LandRecord
    land_rec = db.query(LandRecord).filter(LandRecord.document_id == doc.id).first()
    
    # Retrieve validation results
    validation_results = db.query(ValidationResult).filter(ValidationResult.document_id == doc.id).all()
    
    return {
        "document": {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "file_path": file_url,
            "preprocessed_path": doc.preprocessed_path,
            "doc_type": doc.doc_type,
            "language": doc.language,
            "format_type": doc.format_type,
            "status": doc.status,
            "confidence_score": doc.confidence_score,
            "processing_stage": doc.processing_stage,
            "ocr_text": doc.ocr_text,
            "created_at": doc.created_at
        },
        "land_record": land_rec,
        "validation_results": validation_results
    }
