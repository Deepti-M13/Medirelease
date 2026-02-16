from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import json
from datetime import datetime
from database import get_db, User, DailyLog, AdminReport, DischargeSummary, Bill, PatientTimeline, MedicineLog, DoctorVisit
from pydantic import BaseModel
from services.medicine_analyzer import MEDICINE_MAPPING, load_medicine_mapping
from auth import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])

class DailyUpdate(BaseModel):
    patient_id: int
    update_text: str
    medications: str  # Comma separated or JSON

class MedicineLogRequest(BaseModel):
    patient_id: int
    medicine_name: str
    quantity: int
    duration: int

class AddPatientRequest(BaseModel):
    username: str
    password: str
    age: int
    gender: str
    contact: Optional[str] = None
    treating_doctor_id: Optional[int] = None

class UpdatePatientDetailsRequest(BaseModel):
    # patient_id is taken from the URL path; body only needs fields to update
    age: Optional[int] = None
    gender: Optional[str] = None
    treating_doctor_id: Optional[int] = None

class SetDoctorFeeRequest(BaseModel):
    doctor_id: int
    fee: float

class RecordVisitRequest(BaseModel):
    patient_id: int
    doctor_id: int

def log_timeline_event(db: Session, patient_id: int, event_type: str, description: str):
    """Helper to add timeline event"""
    event = PatientTimeline(
        patient_id=patient_id,
        event_type=event_type,
        description=description
    )
    db.add(event)
    db.commit()

class PatientResponse(BaseModel):
    id: int
    username: str
    role: str
    
# --- Admin Endpoints ---

@router.post("/add-patient")
async def add_patient(
    req: AddPatientRequest,
    db: Session = Depends(get_db)
):
    """Add a new patient to the system"""
    # Validate inputs
    if req.age is None or req.age <= 0:
        raise HTTPException(status_code=400, detail="Age must be a positive integer")
    if not req.gender:
        raise HTTPException(status_code=400, detail="Gender is required")

    # Check if patient already exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient already exists")

    # If treating doctor specified, verify exists
    if req.treating_doctor_id is not None:
        doctor = db.query(User).filter(User.id == req.treating_doctor_id, User.role == "doctor").first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Assigned doctor not found")

    # Create user using create_user helper
    from auth import create_user
    new_patient = create_user(
        db,
        req.username,
        req.password,
        "patient",
        age=req.age,
        gender=req.gender,
        contact=req.contact,
        treating_doctor_id=req.treating_doctor_id
    )

    return {
        "message": "Patient added successfully",
        "patient_id": new_patient.id,
        "username": new_patient.username
    }

@router.get("/patients")
async def get_all_patients(db: Session = Depends(get_db)):
    """List all patients for admin dashboard with detailed information"""
    patients = db.query(User).filter(User.role.in_(["patient", "past_patient"])).all()
    result = []
    for p in patients:
        doctor_name = None
        if p.treating_doctor_id:
            doctor = db.query(User).filter(User.id == p.treating_doctor_id).first()
            if doctor:
                doctor_name = doctor.username
        
        result.append({
            "id": p.id,
            "username": p.username,
            "role": p.role,
            "age": p.age,
            "gender": p.gender,
            "treating_doctor": doctor_name,
            "treating_doctor_id": p.treating_doctor_id,
            "created_at": p.created_at
        })
    return result


@router.get("/doctors")
async def get_all_doctors(db: Session = Depends(get_db)):
    """List all doctors for admin dashboard"""
    doctors = db.query(User).filter(User.role == "doctor").all()
    result = []
    for doc in doctors:
        result.append({
            "id": doc.id,
            "username": doc.username,
            "role": doc.role
        })
    return result

@router.put("/patient/{patient_id}/details")
async def update_patient_details(
    patient_id: int,
    req: UpdatePatientDetailsRequest,
    db: Session = Depends(get_db)
):
    """Update patient details including age, gender, and treating doctor"""
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if req.age is not None:
        patient.age = req.age
    if req.gender is not None:
        patient.gender = req.gender
    if req.treating_doctor_id is not None:
        # Verify doctor exists
        doctor = db.query(User).filter(User.id == req.treating_doctor_id, User.role == "doctor").first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        patient.treating_doctor_id = req.treating_doctor_id
    
    db.commit()
    db.refresh(patient)
    return {
        "message": "Patient details updated successfully",
        "patient_id": patient.id,
        "age": patient.age,
        "gender": patient.gender,
        "treating_doctor_id": patient.treating_doctor_id
    }

@router.post("/daily-update")
async def add_daily_update(
    update: DailyUpdate,
    db: Session = Depends(get_db)
):
    """Add a daily health update and medication log for a patient"""
    # Verify patient exists
    patient = db.query(User).filter(User.id == update.patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    log = DailyLog(
        patient_id=update.patient_id,
        update_text=update.update_text,
        medications=update.medications,
        # In a real app we'd get the admin ID from auth, for MVP using 1 or None
        created_by=1 
    )
    db.add(log)
    db.commit()
    
    # Auto-log to timeline
    log_timeline_event(db, update.patient_id, "Daily Update", update.update_text)
    
    return {"message": "Daily update added successfully", "id": log.id}

@router.post("/upload-report")
async def upload_admin_report(
    patient_id: int = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a medical report for a patient"""
    # Verify patient
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Save file
    UPLOAD_DIR = "uploads/reports"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_path = os.path.join(UPLOAD_DIR, f"{patient_id}_{int(datetime.now().timestamp())}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    report = AdminReport(
        patient_id=patient_id,
        description=description,
        file_path=file_path,
        created_by=1
    )
    db.add(report)
    db.commit()
    
    db.add(report)
    db.commit()
    
    # Auto-log to timeline
    log_timeline_event(db, patient_id, "Report Uploaded", f"Report: {description}")
    
    return {"message": "Report uploaded successfully", "id": report.id}


@router.post("/log-medicine")
async def log_medicine(
    req: MedicineLogRequest,
    db: Session = Depends(get_db)
):
    """Log medicine given to patient and calculate cost"""
    # Ensure mapping is loaded
    if not MEDICINE_MAPPING:
        load_medicine_mapping()
        
    # Lookup price
    med_name_lower = req.medicine_name.lower()
    unit_price = 0.0
    generic_name = "Unknown"
    
    # Simple lookup logic (can be enhanced)
    found_info = None
    for brand, info in MEDICINE_MAPPING.items():
        if brand in med_name_lower:
            found_info = info
            break
            
    if found_info:
        unit_price = found_info['expected_price']
        generic_name = found_info['generic_name']
    else:
        # Fallback or Estimated
        unit_price = 10.0 # Default fallback
        generic_name = "Generic (Est)"
        
    subtotal = unit_price * req.quantity
    
    med_log = MedicineLog(
        patient_id=req.patient_id,
        medicine_name=req.medicine_name,
        generic_name=generic_name,
        unit_price=unit_price,
        quantity=req.quantity,
        duration=req.duration,
        subtotal=subtotal
    )
    db.add(med_log)
    db.commit()
    
    # Add to timeline
    log_timeline_event(db, req.patient_id, "Medication", f"Given {req.medicine_name} (Qty: {req.quantity})")
    
    return {"message": "Medicine logged", "subtotal": subtotal}

@router.post("/set-doctor-fee")
async def set_doctor_fee(req: SetDoctorFeeRequest, db: Session = Depends(get_db)):
    """Set consultation fee for a doctor"""
    doctor = db.query(User).filter(User.id == req.doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    doctor.consultation_fee = req.fee
    db.commit()
    return {"message": f"Consultation fee for {doctor.username} set to ₹{req.fee}"}

@router.post("/record-visit")
async def record_visit(req: RecordVisitRequest, db: Session = Depends(get_db)):
    """Record a doctor visit for a patient"""
    patient = db.query(User).filter(User.id == req.patient_id, User.role.in_(["patient", "past_patient"])).first()
    doctor = db.query(User).filter(User.id == req.doctor_id, User.role == "doctor").first()
    
    if not patient or not doctor:
        raise HTTPException(status_code=404, detail="Patient or Doctor not found")
    
    visit = DoctorVisit(
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        fee_at_time_of_visit=doctor.consultation_fee
    )
    db.add(visit)
    db.commit()
    
    # Add to timeline
    log_timeline_event(db, req.patient_id, "Doctor Visit", f"Visited by Dr. {doctor.username}")
    
    return {"message": f"Visit by Dr. {doctor.username} recorded"}

@router.get("/patient/{patient_id}/timeline")
async def get_patient_timeline(patient_id: int, db: Session = Depends(get_db)):
    """Get full timeline including daily logs, reports, and medicines"""
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
async def get_system_cost_summary(patient_id: int, db: Session = Depends(get_db)):
    """
    Generate an estimated cost summary excluding room/nursing.
    Includes medication costs and doctor consultation fees.
    """
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

