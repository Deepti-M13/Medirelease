from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import init_db, get_db, User
from auth import authenticate_user, create_user, hash_password, verify_password
from routers import doctor, patient, bill_processing, admin, public
import sys
import asyncio

from fastapi.staticfiles import StaticFiles
import os

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Web Application",
    description="A role-based healthcare app for doctors and patients",
    version="1.0.0"
)

# CORS middleware for frontend
import os
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Set CORS_ORIGINS env var in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory to serve static files (reports)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(doctor.router)
app.include_router(patient.router)
app.include_router(bill_processing.router)
app.include_router(admin.router)
app.include_router(public.router)
from routers import prescription
app.include_router(prescription.router)


# Models
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str  # 'doctor', 'patient', 'admin'


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    user_id: int
    old_password: str
    new_password: str


class ChangeUsernameRequest(BaseModel):
    user_id: int
    new_username: str
    password: str


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Healthcare application started successfully!")
    print("Database initialized.")
    
    # Create sample users if they don't exist
    from database import SessionLocal, User, DailyLog, MedicineLog, AdminReport
    from datetime import datetime, timedelta
    db = SessionLocal()
    
    try:
        # Check if users exist
        doctor_user = db.query(User).filter(User.username == "doctor1").first()
        if not doctor_user:
            create_user(db, "doctor1", "password123", "doctor")
            doctor_user = db.query(User).filter(User.username == "doctor1").first()
            print("Created sample doctor: doctor1 / password123")
        
        patient_user = db.query(User).filter(User.username == "patient1").first()
        if not patient_user:
            create_user(db, "patient1", "password123", "patient", age=35, gender="Male")
            patient_user = db.query(User).filter(User.username == "patient1").first()
            print("Created sample patient: patient1 / password123")

        if not db.query(User).filter(User.username == "admin1").first():
            create_user(db, "admin1", "password123", "admin")
            print("Created sample admin: admin1 / password123")
        
        # Add sample timeline data for patient1
        if patient_user and db.query(DailyLog).filter(DailyLog.patient_id == patient_user.id).count() == 0:
            # Add daily log
            daily_log = DailyLog(
                patient_id=patient_user.id,
                update_text="Patient showing good recovery. Vitals stable. Oxygen saturation normal.",
                medications="Antibiotics, Pain relievers, Vitamins",
                created_at=datetime.now() - timedelta(days=2)
            )
            db.add(daily_log)
            
            # Add medicine logs
            for i in range(3):
                med = MedicineLog(
                    patient_id=patient_user.id,
                    medicine_name=["Amoxicillin", "Paracetamol", "Vitamin B12"][i],
                    generic_name=["Amoxicillin 500mg", "Paracetamol 500mg", "Cyanocobalamin 1000mcg"][i],
                    quantity=[10, 15, 30][i],
                    duration=[10, 7, 30][i],
                    unit_price=[5.0, 2.5, 3.0][i],
                    subtotal=[50.0, 37.5, 90.0][i],
                    timestamp=datetime.now() - timedelta(days=1-i)
                )
                db.add(med)
            
            db.commit()
            print("Added sample timeline data for patient1")
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Healthcare Web Application API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint
    
    Validates credentials and returns user info
    """
    user = authenticate_user(db, request.username, request.password, request.role)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials or role mismatch"
        )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Login successful"
    }


@app.post("/api/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    from database import User
    
    # Check if user exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    
    # Validate role
    if request.role not in ['doctor', 'patient', 'admin']:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be 'doctor', 'patient', or 'admin'"
        )
    
    # Create user
    user = create_user(db, request.username, request.password, request.role)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Registration successful"
    }


@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    """
    Change user password
    """
    # Get user
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Verify old password
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid old password"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {
        "message": "Password changed successfully"
    }


@app.post("/api/auth/change-username")
async def change_username(request: ChangeUsernameRequest, db: Session = Depends(get_db)):
    """
    Change user username
    """
    # Get user
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
    
    # Check if new username already exists
    existing = db.query(User).filter(User.username == request.new_username).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Update username
    user.username = request.new_username
    db.commit()
    
    # Return updated user info for localStorage update
    return {
        "message": "Username changed successfully",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
