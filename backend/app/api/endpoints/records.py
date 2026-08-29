import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.core.dependencies import get_db, get_current_active_user
from app.models.land_records import LandRecord
from app.models.documents import Document
from app.schemas.land_records import LandRecordResponse, LandRecordDetailResponse

router = APIRouter(prefix="/records", tags=["Land Records"])

@router.get("", response_model=List[LandRecordResponse])
def search_records(
    q: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    survey_number: Optional[str] = Query(None),
    khata_number: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(LandRecord)
    if q:
        query = query.filter(
            (LandRecord.owner_name.ilike(f"%{q}%")) |
            (LandRecord.survey_number.ilike(f"%{q}%")) |
            (LandRecord.khata_number.ilike(f"%{q}%")) |
            (LandRecord.village.ilike(f"%{q}%"))
        )
    if village:
        query = query.filter(LandRecord.village.ilike(f"%{village}%"))
    if district:
        query = query.filter(LandRecord.district.ilike(f"%{district}%"))
    if status:
        query = query.filter(LandRecord.verification_status == status)
    if survey_number:
        query = query.filter(LandRecord.survey_number == survey_number)
    if khata_number:
        query = query.filter(LandRecord.khata_number == khata_number)

    return query.order_by(LandRecord.updated_at.desc()).offset(skip).limit(limit).all()

@router.get("/export/csv")
def export_records_csv(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    records = db.query(LandRecord).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "Owner Name", "Survey No", "Khasra No", "Khata No", 
        "Area", "Unit", "Village", "Tehsil/Mandal", "District", "Status", "Registration Date"
    ])
    for r in records:
        writer.writerow([
            r.id, r.owner_name, r.survey_number, r.khasra_number, r.khata_number,
            r.area, r.area_unit, r.village, r.tehsil_mandal, r.district, r.verification_status, r.registration_date
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=land_records_export.csv"}
    )

@router.get("/export/pdf/{record_id}")
def export_record_pdf(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    record = db.query(LandRecord).filter(LandRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Land record not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>GOVERNMENT LAND RECORD CERTIFICATE</b>", styles['Heading1']))
    elements.append(Paragraph(f"Digitized & Verified Land Ownership Document - ID #{record.id}", styles['Normal']))
    elements.append(Spacer(1, 14))

    data = [
        ["Field", "Digitized Record Value"],
        ["Owner Name", record.owner_name or "N/A"],
        ["Survey Number", record.survey_number or "N/A"],
        ["Khata Number", record.khata_number or "N/A"],
        ["Khasra Number", record.khasra_number or "N/A"],
        ["Area / Extent", f"{record.area or 'N/A'} {record.area_unit or ''}"],
        ["Village", record.village or "N/A"],
        ["Tehsil/Mandal", record.tehsil_mandal or "N/A"],
        ["District", record.district or "N/A"],
        ["Classification", record.land_classification or "N/A"],
        ["Status", record.verification_status or "N/A"]
    ]

    t = Table(data, colWidths=[180, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=LandRecord_{record.id}.pdf"}
    )

@router.get("/{record_id}", response_model=LandRecordDetailResponse)
def get_record_details(
    record_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    rec = db.query(LandRecord).filter(LandRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Land record not found")
        
    doc = db.query(Document).filter(Document.id == rec.document_id).first()
    return {"record": rec, "document": doc}
