from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str, role: str):
    """Authenticate a user and verify role"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    if user.role != role:
        # Allow 'past_patient' to login as 'patient'
        if not (role == 'patient' and user.role == 'past_patient'):
            return None
    
    return user


def create_user(db: Session, username: str, password: str, role: str, age: int = None, gender: str = None, contact: str = None, treating_doctor_id: int = None):
    """Create a new user"""
    hashed_pw = hash_password(password)
    user = User(
        username=username,
        password_hash=hashed_pw,
        role=role,
        age=age,
        gender=gender,
        contact=contact,
        treating_doctor_id=treating_doctor_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()
