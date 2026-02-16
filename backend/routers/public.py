from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from services.bill_analyzer import extract_text_from_file
from services.medicine_analyzer import extract_medicine_names, load_medicine_mapping, MEDICINE_MAPPING

router = APIRouter(prefix="/api/public", tags=["public"])

UPLOAD_DIR = "uploads/temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/predict-price")
async def predict_generic_price(file: UploadFile = File(...)):
    """
    Public endpoint: Upload prescription -> Extract medicines -> Show Generic Prices
    """
    try:
        # Save file temporarily
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract text
        text = extract_text_from_file(file_path)
        
        # Extract medicines
        medicine_names = extract_medicine_names(text)
        
        # Map to generics
        load_medicine_mapping()
        
        results = []
        
        for med_name in medicine_names:
            found = False
            for brand, info in MEDICINE_MAPPING.items():
                # Simple containment check
                if brand in med_name.lower():
                    results.append({
                        "found_name": med_name,
                        "brand_match": brand.title(),
                        "generic_name": info['generic_name'],
                        "reference_price": info['expected_price'],
                        "unit": info['unit'],
                        "savings_note": "Significant savings possible with generic."
                    })
                    found = True
                    break
            
            if not found:
                # Still return the name so user sees we found it
                results.append({
                    "found_name": med_name,
                    "brand_match": None,
                    "generic_name": "Not found in database",
                    "reference_price": None,
                    "unit": None
                })
                
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
            
        return {
            "medicines_found": len(results),
            "predictions": results,
            "disclaimer": "Prices are indicative reference rates for generic medicines."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
