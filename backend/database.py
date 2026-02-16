from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./healthcare.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'doctor', 'patient', 'admin'
    age = Column(Integer)  # For patients
    gender = Column(String(20))  # For patients: 'M', 'F', 'Other'
    treating_doctor_id = Column(Integer, ForeignKey('users.id'))  # For patients - who is treating them
    contact = Column(String(100))  # Optional contact details (phone/email)
    consultation_fee = Column(Float, default=500.0)  # For doctors
    created_at = Column(DateTime, default=datetime.utcnow)


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Link to patient
    patient_name = Column(String(200), nullable=False)
    summary_text = Column(Text, nullable=False)
    follow_up = Column(Text)
    diet_advice = Column(Text)
    red_flags = Column(Text)
    reports_path = Column(String(500))  # Store path to uploaded medical reports
    status = Column(String(20), default='draft')  # 'draft' or 'final'
    created_by = Column(Integer, ForeignKey('users.id'))  # Doctor who created it
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(500))
    extracted_text = Column(Text)
    analysis_result = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    medicine_analyses = relationship("MedicineAnalysis", back_populates="bill")


class MedicineAnalysis(Base):
    __tablename__ = "medicine_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey('bills.id'), nullable=False)
    brand_name = Column(String(200))
    generic_name = Column(String(200))
    billed_price = Column(Float)
    expected_price = Column(Float)
    excess = Column(Float)
    
    bill = relationship("Bill", back_populates="medicine_analyses")


class DailyLog(Base):
    __tablename__ = "daily_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_text = Column(Text, nullable=False)
    medications = Column(Text)  # JSON string or simple text list of meds given
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))  # Admin who created it


class AdminReport(Base):
    __tablename__ = "admin_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(500), nullable=False)
    description = Column(String(200))
    current_condition = Column(String(200)) # e.g., "Stable", "Critical"
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))


class PatientTimeline(Base):
    __tablename__ = "patient_timeline"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'Report', 'Daily Update', 'Medication'
    description = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DoctorVisit(Base):
    __tablename__ = "doctor_visits"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    fee_at_time_of_visit = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MedicineLog(Base):
    __tablename__ = "medicine_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    medicine_name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    unit_price = Column(Float, default=0.0)
    quantity = Column(Integer, default=1)
    duration = Column(Integer, default=1) # days
    subtotal = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize the database and create tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
