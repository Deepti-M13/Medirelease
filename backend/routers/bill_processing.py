from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict
import shutil
import os
import uuid
from services.bill_analyzer import analyze_bill

router = APIRouter(
    prefix="/api/bills",
    tags=["bills"]
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze")
async def analyze_uploaded_bill(file: UploadFile = File(...)):
    """
    Upload and analyze a medical bill
    """
    try:
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Analyze bill
        result = analyze_bill(file_path)
        
        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
             
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
