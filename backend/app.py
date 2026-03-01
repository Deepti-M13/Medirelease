from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from database import init_db, get_db, User
from auth import authenticate_user, create_user, hash_password, verify_password
from routers import doctor, patient, bill_processing, admin, public, prescription

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="Healthcare Web Application",
    description="A role-based healthcare app for doctors and patients",
    version="1.0.0"
)

# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Static Files (Uploads)
# --------------------------------------------------

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --------------------------------------------------
# Include Routers
# --------------------------------------------------

app.include_router(doctor.router)
app.include_router(patient.router)
app.include_router(bill_processing.router)
app.include_router(admin.router)
app.include_router(public.router)
app.include_router(prescription.router)

# --------------------------------------------------
# Request Models
# --------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str


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


# --------------------------------------------------
# Startup Event
# --------------------------------------------------

@app.on_event("startup")
async def startup_event():
    init_db()
    print("Healthcare application started successfully!")
    print("Database initialized.")


# --------------------------------------------------
# Root & Health
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Healthcare Web Application API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# Authentication APIs
# --------------------------------------------------

@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
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
    existing_user = db.query(User).filter(User.username == request.username).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    if request.role not in ['doctor', 'patient', 'admin']:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    user = create_user(db, request.username, request.password, request.role)

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Registration successful"
    }


@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid old password")

    user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@app.post("/api/auth/change-username")
async def change_username(request: ChangeUsernameRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    existing = db.query(User).filter(User.username == request.new_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user.username = request.new_username
    db.commit()

        return {
        "message": "Username changed successfully",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }
    
>>>>>>> 278ee3a (Update project files and set Python 3.11)
