from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.land_records import LandRecord
from app.models.documents import Document
from app.schemas.land_records import LandRecordResponse, LandRecordUpdate
from app.dependencies import get_current_active_user

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter(prefix="/records", tags=["Land Records"])

@router.get("", response_model=list[LandRecordResponse])
def search_records(
    db: Session = Depends(get_db),
    owner_name: Optional[str] = Query(None),
    survey_number: Optional[str] = Query(None),
    khata_number: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    tehsil_mandal: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    current_user = Depends(get_current_active_user)
):
    query = db.query(LandRecord)
    
    if owner_name:
        query = query.filter(LandRecord.owner_name.ilike(f"%{owner_name}%"))
    if survey_number:
        query = query.filter(LandRecord.survey_number.ilike(f"%{survey_number}%"))
    if khata_number:
        query = query.filter(LandRecord.khata_number == khata_number)
    if village:
        query = query.filter(LandRecord.village.ilike(f"%{village}%"))
    if tehsil_mandal:
        query = query.filter(LandRecord.tehsil_mandal.ilike(f"%{tehsil_mandal}%"))
    if district:
        query = query.filter(LandRecord.district.ilike(f"%{district}%"))
    if verification_status:
        query = query.filter(LandRecord.verification_status == verification_status)
        
    return query.order_by(LandRecord.updated_at.desc()).all()


@router.get("/{record_id}", response_model=LandRecordResponse)
def get_record(
    record_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    record = db.query(LandRecord).filter(LandRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Land record not found")
    return record


@router.get("/export/csv")
def export_records_csv(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """Export all verified land records to CSV."""
    records = db.query(LandRecord).filter(LandRecord.verification_status == "Verified").all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Record ID", "Owner Name", "Survey Number", "Khasra Number", "Khata Number", 
        "Plot Number", "Area", "Area Unit", "Village", "Tehsil/Mandal", "District", 
        "Land Classification", "Ownership Type", "Mutation Number", "Registration Number", 
        "Registration Date", "Verification Status", "Digitization Date"
    ])
    
    # Rows
    for r in records:
        writer.writerow([
            r.id, r.owner_name, r.survey_number, r.khasra_number, r.khata_number,
            r.plot_number, r.area, r.area_unit, r.village, r.tehsil_mandal, r.district,
            r.land_classification, r.ownership_type, r.mutation_number, r.registration_number,
            r.registration_date, r.verification_status, r.created_at.strftime("%Y-%m-%d")
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=digitized_land_records.csv"}
    )


@router.get("/export/pdf/{record_id}")
def export_record_pdf(
    record_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """Generate a formal PDF certificate for a verified land record."""
    record = db.query(LandRecord).filter(LandRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Land record not found")
        
    doc_meta = db.query(Document).filter(Document.id == record.document_id).first() if record.document_id else None
    
    buffer = io.BytesIO()
    pdf_doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'), # Navy blue
        alignment=1 # Centered
    )
    
    subtitle_style = ParagraphStyle(
        'GovSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'), # Slate grey
        alignment=1
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f766e'), # Teal
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    bold_style = ParagraphStyle(
        'BoldText',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []
    
    # 1. Header Header
    story.append(Paragraph("GOVERNMENT OF TELANGANA / ANDHRA PRADESH", subtitle_style))
    story.append(Paragraph("DEPARTMENT OF LAND REVENUE, SURVEY & SETTLEMENTS", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("CERTIFICATE OF DIGITIZED LAND RECORD", title_style))
    story.append(Spacer(1, 15))
    
    # Decorative line
    line_data = [['']]
    line_table = Table(line_data, colWidths=[540])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#1e3a8a')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))
    
    # 2. General metadata
    meta_info = [
        [Paragraph("Record Reference ID:", bold_style), Paragraph(f"DIG-LR-{record.id:06d}", body_style),
         Paragraph("Date of Digitization:", bold_style), Paragraph(record.created_at.strftime("%d-%m-%Y %H:%M"), body_style)],
        [Paragraph("Verification Status:", bold_style), Paragraph(record.verification_status.upper(), bold_style),
         Paragraph("Original Filename:", bold_style), Paragraph(doc_meta.original_filename if doc_meta else "Legacy Record", body_style)]
    ]
    meta_table = Table(meta_info, colWidths=[120, 150, 120, 150])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 3. Location Details Section
    story.append(Paragraph("Location Hierarchy", section_style))
    location_info = [
        [Paragraph("District", bold_style), Paragraph(record.district or "N/A", body_style),
         Paragraph("Tehsil / Mandal", bold_style), Paragraph(record.tehsil_mandal or "N/A", body_style),
         Paragraph("Village", bold_style), Paragraph(record.village or "N/A", body_style)]
    ]
    location_table = Table(location_info, colWidths=[90, 90, 90, 90, 90, 90])
    location_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (2,0), (2,0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (4,0), (4,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(location_table)
    story.append(Spacer(1, 15))
    
    # 4. Property Specifications
    story.append(Paragraph("Land Property Specifications", section_style))
    property_info = [
        [Paragraph("Pattadar / Owner Name", bold_style), Paragraph(record.owner_name or "N/A", body_style)],
        [Paragraph("Survey Number", bold_style), Paragraph(record.survey_number or "N/A", body_style)],
        [Paragraph("Khasra Number", bold_style), Paragraph(record.khasra_number or "N/A", body_style)],
        [Paragraph("Khata Number", bold_style), Paragraph(record.khata_number or "N/A", body_style)],
        [Paragraph("Plot Number", bold_style), Paragraph(record.plot_number or "N/A", body_style)],
        [Paragraph("Registered Area / Extent", bold_style), Paragraph(f"{record.area or 0.0} {record.area_unit}", body_style)],
        [Paragraph("Land Classification", bold_style), Paragraph(record.land_classification or "N/A", body_style)],
        [Paragraph("Ownership Type", bold_style), Paragraph(record.ownership_type or "N/A", body_style)]
    ]
    
    # Add mutation/reg details if available
    if record.mutation_number:
        property_info.append([Paragraph("Mutation Order Number", bold_style), Paragraph(record.mutation_number, body_style)])
    if record.registration_number:
        property_info.append([Paragraph("Registration Number & Date", bold_style), Paragraph(f"{record.registration_number} dated {record.registration_date}", body_style)])
        
    property_table = Table(property_info, colWidths=[200, 340])
    property_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(property_table)
    story.append(Spacer(1, 30))
    
    # 5. Disclaimer / Signatures
    disclaimer_text = (
        "Disclaimer: This document is an AI-digitized transcript of historical revenue office registers "
        "and has been validated and accepted by a designated Revenue Officer. This copy is generated for "
        "informational/assistance purposes and does not replace the legally authoritative physical titles "
        "held at local Tehsil Registry offices."
    )
    story.append(Paragraph(disclaimer_text, ParagraphStyle('Disc', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#64748b'))))
    story.append(Spacer(1, 40))
    
    # Signatures
    sig_data = [
        [Paragraph("Digitized by System Agent<br/><b>Intelligent Land Record System</b>", body_style),
         Paragraph("Approved by authorized officer<br/><b>Tehsildar / Land Registrar</b>", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(sig_table)
    
    pdf_doc.build(story)
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=land_record_certificate_{record_id}.pdf"}
    )
