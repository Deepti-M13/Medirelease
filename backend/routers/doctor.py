from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, DischargeSummary, DailyLog, AdminReport, MedicineLog, User, DoctorVisit
from services.discharge_summary import generate_discharge_summary
from services.pdf_generator import generate_discharge_summary_pdf
from fastapi.responses import Response

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


class GenerateSummaryRequest(BaseModel):
    patient_name: str
    clinical_notes: str


class UpdateSummaryRequest(BaseModel):
    summary_text: Optional[str] = None
    follow_up: Optional[str] = None
    diet_advice: Optional[str] = None
    red_flags: Optional[str] = None


@router.post("/discharge-summary/generate")
async def create_discharge_summary(
    patient_id: int = Form(...),
    patient_name: str = Form(...),
    clinical_notes: str = Form(...),
    doctor_id: int = Form(...),
    reports: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Generate discharge summary from clinical notes using Groq API
    Supports optional medical report upload
    """
    try:
        # Handle report file if uploaded
        reports_path = None
        if reports:
            import os
            import shutil
            REPORTS_DIR = "uploads/reports"
            os.makedirs(REPORTS_DIR, exist_ok=True)
            reports_path = os.path.join(REPORTS_DIR, reports.filename)
            with open(reports_path, "wb") as buffer:
                shutil.copyfileobj(reports.file, buffer)
        
        # Generate summary using Groq API
        raw_summary_text = generate_discharge_summary(
            clinical_notes,
            patient_name
        )
        
        # Parse into sections
        from services.discharge_summary import parse_summary_sections
        parsed = parse_summary_sections(raw_summary_text)
        
        # Save to database
        summary = DischargeSummary(
            patient_id=patient_id,
            patient_name=patient_name,
            summary_text=parsed['summary_text'],
            follow_up=parsed['follow_up'],
            diet_advice=parsed['diet_advice'],
            red_flags=parsed['red_flags'],
            reports_path=reports_path,
            status='draft',
            created_by=doctor_id
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        return {
            "id": summary.id,
            "patient_id": summary.patient_id,
            "patient_name": summary.patient_name,
            "summary_text": summary.summary_text,
            "reports_path": summary.reports_path,
            "status": summary.status,
            "created_at": summary.created_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )


@router.put("/discharge-summary/{summary_id}")
async def update_discharge_summary(
    summary_id: int,
    request: UpdateSummaryRequest,
    db: Session = Depends(get_db)
):
    """
    Update discharge summary fields
    """
    summary = db.query(DischargeSummary).filter(DischargeSummary.id == summary_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Update fields
    if request.summary_text is not None:
        summary.summary_text = request.summary_text
    if request.follow_up is not None:
        summary.follow_up = request.follow_up
    if request.diet_advice is not None:
        summary.diet_advice = request.diet_advice
    if request.red_flags is not None:
        summary.red_flags = request.red_flags
    
    db.commit()
    db.refresh(summary)
    
    return {
        "id": summary.id,
        "patient_name": summary.patient_name,
        "summary_text": summary.summary_text,
        "follow_up": summary.follow_up,
        "diet_advice": summary.diet_advice,
        "red_flags": summary.red_flags,
        "status": summary.status
    }


@router.post("/discharge-summary/{summary_id}/finalize")
async def finalize_discharge_summary(
    summary_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark discharge summary as final and update patient status
    """
    summary = db.query(DischargeSummary).filter(DischargeSummary.id == summary_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Update summary status
    summary.status = 'final'
    
    # Update patient role to 'past_patient'
    patient = db.query(User).filter(User.id == summary.patient_id).first()
    if patient:
        patient.role = 'past_patient'
        
    db.commit()
    
    return {"message": "Summary marked as final and patient status updated", "id": summary.id}


@router.get("/discharge-summary/{summary_id}/pdf")
async def download_discharge_summary_pdf(
    summary_id: int,
    db: Session = Depends(get_db)
):
    """
    Download discharge summary as PDF
    """
    summary = db.query(DischargeSummary).filter(DischargeSummary.id == summary_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Generate PDF
    pdf_data = {
        'patient_name': summary.patient_name,
        'summary_text': summary.summary_text,
        'follow_up': summary.follow_up or '',
        'diet_advice': summary.diet_advice or '',
        'red_flags': summary.red_flags or ''
    }
    
    pdf_bytes = generate_discharge_summary_pdf(pdf_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=discharge_summary_{summary_id}.pdf"
        }
    )


@router.get("/discharge-summary/{summary_id}")
async def get_discharge_summary(
    summary_id: int,
    db: Session = Depends(get_db)
):
    """
    Get discharge summary by ID
    """
    summary = db.query(DischargeSummary).filter(DischargeSummary.id == summary_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return {
        "id": summary.id,
        "patient_name": summary.patient_name,
        "summary_text": summary.summary_text,
        "follow_up": summary.follow_up,
        "diet_advice": summary.diet_advice,
        "red_flags": summary.red_flags,
        "status": summary.status,
        "created_at": summary.created_at
    }


@router.get("/my-patients")
async def get_doctor_patients(
    doctor_id: int,  # Get from auth in real app
    db: Session = Depends(get_db)
):
    """Get list of patients being treated by this doctor"""
    patients = db.query(User).filter(
        User.role.in_(["patient", "past_patient"]),
        User.treating_doctor_id == doctor_id
    ).all()
    
    result = []
    for p in patients:
        # Get latest discharge summary if exists
        latest_summary = db.query(DischargeSummary).filter(
            DischargeSummary.patient_id == p.id
        ).order_by(DischargeSummary.created_at.desc()).first()
        
        result.append({
            "id": p.id,
            "username": p.username,
            "role": p.role,
            "age": p.age,
            "gender": p.gender,
            "latest_summary_id": latest_summary.id if latest_summary else None,
            "latest_summary_status": latest_summary.status if latest_summary else None,
            "created_at": p.created_at
        })
    
    return result

@router.get("/discharge-summaries")
async def list_discharge_summaries(
    doctor_id: int,  # Get from auth in real app
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    List all discharge summaries created by this doctor
    """
    summaries = db.query(DischargeSummary).filter(
        DischargeSummary.created_by == doctor_id
    ).order_by(DischargeSummary.created_at.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": s.id,
        "patient_id": s.patient_id,
        "patient_name": s.patient_name,
        "status": s.status,
        "created_at": s.created_at,
        "updated_at": s.updated_at
    } for s in summaries]


@router.get("/patient/{patient_id}/timeline")
async def get_patient_timeline_doctor(patient_id: int, db: Session = Depends(get_db)):
    """Doctor can view full patient timeline (daily logs + reports + medicines)"""
    timeline = []
    
    # Get daily logs
    logs = db.query(DailyLog).filter(DailyLog.patient_id == patient_id).all()
    for log in logs:
        timeline.append({
            "type": "Daily Update",
            "date": log.created_at,
            "content": log.update_text,
            "medications": log.medications,
            "id": log.id
        })
    
    # Get reports
    reports = db.query(AdminReport).filter(AdminReport.patient_id == patient_id).all()
    for report in reports:
        timeline.append({
            "type": "Report",
            "date": report.created_at,
            "content": report.description,
            "file_path": report.file_path.replace("\\", "/") if report.file_path else None,
            "id": report.id
        })
    
    # Get medicines
    medicines = db.query(MedicineLog).filter(MedicineLog.patient_id == patient_id).all()
    for med in medicines:
        timeline.append({
            "type": "Medication",
            "date": med.timestamp,
            "content": f"Given {med.medicine_name} (Qty: {med.quantity})",
            "medicine_name": med.medicine_name,
            "quantity": med.quantity,
            "duration": med.duration,
            "generic_name": med.generic_name,
            "unit_price": med.unit_price,
            "subtotal": med.subtotal,
            "id": med.id
        })
        
    timeline.sort(key=lambda x: x['date'], reverse=True)
    return timeline


@router.get("/patient/{patient_id}/cost-summary")
async def get_patient_cost_summary_doctor(patient_id: int, db: Session = Depends(get_db)):
    """Doctor can view patient's cost summary (Medicines & Consultations only)"""
    breakdown = []
    total = 0.0

    # 1. Calculate Medicine Costs
    med_logs = db.query(MedicineLog).filter(MedicineLog.patient_id == patient_id).all()
    med_total = 0
    for med in med_logs:
        med_total += med.subtotal
        breakdown.append({
            "item": f"Medicine: {med.medicine_name}",
            "rate": med.unit_price,
            "quantity": med.quantity,
            "total": med.subtotal
        })
    total += med_total

    # 2. Calculate Doctor Consultation Fees
    visits = db.query(DoctorVisit).filter(DoctorVisit.patient_id == patient_id).all()
    visit_total = 0
    for visit in visits:
        doctor = db.query(User).filter(User.id == visit.doctor_id).first()
        doc_name = doctor.username if doctor else "Unknown Doctor"
        visit_total += visit.fee_at_time_of_visit
        breakdown.append({
            "item": f"Consultation: Dr. {doc_name}",
            "rate": visit.fee_at_time_of_visit,
            "quantity": 1,
            "total": visit.fee_at_time_of_visit
        })
    total += visit_total

    return {
        "patient_id": patient_id,
        "estimated_total": round(total, 2),
        "breakdown": breakdown,
        "visit_count": len(visits),
        "medicine_total": round(med_total, 2),
        "consultation_total": round(visit_total, 2),
        "message": "Cost Summary (Medicines & Consultations only)"
    }
