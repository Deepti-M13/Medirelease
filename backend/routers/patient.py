from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db, Bill, DischargeSummary, DailyLog, AdminReport, MedicineLog, DoctorVisit, User
from services.bill_summarizer import BillSummarizer
from services.bill_analyzer import analyze_bill
from services.medicine_analyzer import analyze_medicine_prices
from services.negotiation import generate_negotiation_summary
from services.pdf_generator import generate_bill_analysis_pdf
from fastapi.responses import Response, FileResponse
import os
import json
import shutil
import mimetypes

router = APIRouter(prefix="/api/patient", tags=["patient"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/bill/upload")
async def upload_bill(
    file: UploadFile = File(...),
    patient_id: int = 1,  # In real app, get from auth
    db: Session = Depends(get_db)
):
    """
    Upload hospital bill (image or PDF) and analyze it
    """
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze bill
        analysis_result = analyze_bill(file_path)
        
        if 'error' in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=analysis_result['error']
            )
            
        # Adapt LLM output to frontend structure
        llm_analysis = analysis_result.get('analysis', {})
        items = llm_analysis.get('items', [])
        
        # Construct categories
        categories = {
            'medicines': [],
            'investigations': [],
            'room_charges': [],
            'procedures': [],
            'consultation': []
        }
        
        # Construct CGHS comparison
        cghs_comparison = {
            'fair_charges': [],
            'overcharged': [],
            'total_excess': llm_analysis.get('total_overcharged_amount', 0)
        }
        
        # Construct Medicine analysis
        medicine_analysis = []
        
        for item in items:
            cat_lower = item['category'].lower()
            
            # Map items to categories
            mapped_item = {
                'description': item['name'],
                'amount': item['billed_price']
            }
            
            if 'medicine' in cat_lower:
                categories['medicines'].append(mapped_item)
                
                # Add to medicine analysis
                med_entry = {
                    'brand_name': item['name'],
                    'generic_name': item.get('reason', 'Generic check available in detailed report'), # Fallback
                    'billed_price': item['billed_price'],
                    'expected_price': item['expected_price'],
                    'excess': item['excess_amount'],
                    'status': item['status']
                }
                medicine_analysis.append(med_entry)
                
            elif 'investigation' in cat_lower or 'lab' in cat_lower:
                categories['investigations'].append(mapped_item)
            elif 'room' in cat_lower:
                categories['room_charges'].append(mapped_item)
            elif 'procedure' in cat_lower:
                categories['procedures'].append(mapped_item)
            elif 'consultation' in cat_lower:
                categories['consultation'].append(mapped_item)
                
            # Map to CGHS/fairness comparison
            if item['status'].lower() == 'overcharged':
                cghs_comparison['overcharged'].append({
                    'category': item['category'],
                    'description': item['name'],
                    'billed_amount': item['billed_price'],
                    'cghs_rate': item['expected_price'], # Using expected as proxy for rate
                    'excess': item['excess_amount']
                })
            else:
                cghs_comparison['fair_charges'].append({
                    'category': item['category'],
                    'description': item['name'],
                    'amount': item['billed_price']
                })

        # Add negotiation suggestions
        overcharged_list = cghs_comparison['overcharged']
        negotiation_info = generate_negotiation_summary(overcharged_list)
        
        # Combine all analysis
        full_analysis = {
            'categories': categories,
            'cghs_comparison': cghs_comparison,
            'medicine_analysis': medicine_analysis,
            'negotiation': negotiation_info,
            'llm_summary': llm_analysis.get('summary', '') # Store the summary too
        }
        
        # Save to database
        bill = Bill(
            patient_id=patient_id,
            file_path=file_path,
            extracted_text=analysis_result['extracted_text'],
            analysis_result=json.dumps(full_analysis)
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        return {
            "bill_id": bill.id,
            "message": "Bill uploaded and analyzed successfully",
            "analysis": full_analysis
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bill: {str(e)}"
        )


@router.get("/bill/{bill_id}/analysis")
async def get_bill_analysis(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get bill analysis results
    """
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    analysis = json.loads(bill.analysis_result)
    
    return {
        "bill_id": bill.id,
        "analysis": analysis
    }

@router.get("/bill-summary")
async def get_patient_bill_summary_endpoint(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Automatic bill summary based on MedicineLog and web scraping
    """
    summarizer = BillSummarizer(db)
    summary = await summarizer.get_patient_bill_summary(patient_id)
    return summary


@router.get("/medicine-analysis/{bill_id}")
async def get_medicine_analysis(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get medicine price analysis for a bill
    """
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    analysis = json.loads(bill.analysis_result)
    medicine_analysis = analysis.get('medicine_analysis', [])
    
    return {
        "bill_id": bill.id,
        "medicine_analysis": medicine_analysis
    }


@router.get("/discharge-summary/{summary_id}")
async def view_discharge_summary(
    summary_id: int,
    db: Session = Depends(get_db)
):
    """
    View discharge summary (read-only for patients)
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


@router.get("/bill/{bill_id}/pdf")
async def download_bill_analysis_pdf(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Download bill analysis as PDF
    """
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    analysis = json.loads(bill.analysis_result)
    
    # Generate PDF
    pdf_bytes = generate_bill_analysis_pdf(analysis)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=bill_analysis_{bill_id}.pdf"
        }
    )


@router.get("/bills")
async def list_bills(
    patient_id: int = 1,  # In real app, get from auth
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    List all bills for a patient
    """
    bills = db.query(Bill).filter(Bill.patient_id == patient_id).offset(skip).limit(limit).all()
    
    return [{
        "id": b.id,
        "created_at": b.created_at
    } for b in bills]


@router.get("/timeline")
async def get_patient_timeline(
    patient_id: int,  # Required parameter from query
    db: Session = Depends(get_db)
):
    """Get patient's own timeline (daily logs + reports + medicines)"""
    logs = db.query(DailyLog).filter(DailyLog.patient_id == patient_id).all()
    reports = db.query(AdminReport).filter(AdminReport.patient_id == patient_id).all()
    medicines = db.query(MedicineLog).filter(MedicineLog.patient_id == patient_id).all()
    
    timeline = []
    
    for log in logs:
        timeline.append({
            "type": "Daily Update",
            "date": log.created_at,
            "content": log.update_text,
            "medications": log.medications,
            "id": log.id
        })
        
    for report in reports:
        timeline.append({
            "type": "Report",
            "date": report.created_at,
            "content": report.description,
            "file_path": report.file_path,
            "id": report.id
        })
    
    for med in medicines:
        timeline.append({
            "type": "Medication",
            "date": med.timestamp,
            "content": f"Medicine: {med.medicine_name}",
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


@router.get("/cost-summary")
async def get_cost_summary(
    patient_id: int,  # Required parameter from query
    db: Session = Depends(get_db)
):
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
        "message": "This is a system-generated cost summary for reference only."
    }


@router.get("/reports")
async def get_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get all medical reports uploaded for the patient"""
    reports = db.query(AdminReport).filter(AdminReport.patient_id == patient_id).all()
    
    report_list = []
    for report in reports:
        report_list.append({
            "id": report.id,
            "description": report.description,
            "file_path": report.file_path,
            "condition": report.current_condition,
            "created_at": report.created_at.isoformat() if report.created_at else None
        })
    
    return report_list

@router.get("/report/{report_id}")
async def get_report_file(
    report_id: int,
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Serve a specific report file to the patient"""
    # Verify the report belongs to this patient
    report = db.query(AdminReport).filter(
        AdminReport.id == report_id,
        AdminReport.patient_id == patient_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    file_path = report.file_path
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on server"
        )
    
    # Determine media type based on file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type=mime_type
    )


@router.get("/discharge-summaries")
async def get_patient_discharge_summaries(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get finalized discharge summaries for the patient"""
    summaries = db.query(DischargeSummary).filter(
        DischargeSummary.patient_id == patient_id,
        DischargeSummary.status == 'final'
    ).order_by(DischargeSummary.created_at.desc()).all()
    
    return [{
        "id": s.id,
        "patient_name": s.patient_name,
        "summary_text": s.summary_text,
        "follow_up": s.follow_up,
        "diet_advice": s.diet_advice,
        "red_flags": s.red_flags,
        "status": s.status,
        "created_at": s.created_at
    } for s in summaries]
