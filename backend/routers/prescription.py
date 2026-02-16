from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import extract_text_from_image, clean_medicine_name
from services.scraper_service import ScraperService
import shutil
import os
import aiofiles

router = APIRouter(
    prefix="/api/prescription",
    tags=["prescription"]
)

@router.post("/compare-prices-manual")
async def compare_prices_manual(data: dict):
    """
    Directly compare prices for a list of medicine names.
    """
    try:
        medicine_names = data.get("medicine_names", [])
        if not medicine_names:
             raise HTTPException(status_code=400, detail="No medicine names provided.")
        
        # 2. Scrape & Compare
        scraper = ScraperService()
        comparison_results = await scraper.compare_prices(medicine_names)
        
        return {
            "medicines_found": medicine_names,
            "results": comparison_results
        }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"Error in manual price comparison:\n{error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/compare-prices")
async def compare_prices(file: UploadFile = File(...)):
    """
    Upload a prescription image, extract medicine names via OCR,
    and compare prices across multiple pharmacies.
    """
    try:
        # Read image content
        content = await file.read()
        
        # 1. OCR Extraction
        print(f"Processing prescription image: {file.filename}")
        raw_text = ""
        try:
            raw_text = extract_text_from_image(content)
        except Exception as ocr_err:
            print(f"OCR failed: {ocr_err}")
            raise HTTPException(status_code=400, detail="OCR service failed. Make sure Tesseract OCR is installed on the server.")

        print(f"OCR extracted text: {raw_text[:200] if raw_text else 'NONE'}")
        
        if not raw_text:
            raise HTTPException(
                status_code=400, 
                detail="OCR extraction failed. Could not read any text from the image. \n"
                       "Possible reasons:\n"
                       "1. Tesseract OCR is not installed on the server.\n"
                       "2. The image is too blurry or low quality.\n"
                       "Please try 'Enter Manually' mode as a fallback."
            )
            
        medicine_names = clean_medicine_name(raw_text)
        print(f"Cleaned medicine names: {medicine_names}")
        
        if not medicine_names:
             raise HTTPException(
                 status_code=400, 
                 detail="No medicine names could be identified in the prescription text. \n"
                        "Please try 'Enter Manually' mode."
             )
        
        # 2. Scrape & Compare
        scraper = ScraperService()
        comparison_results = await scraper.compare_prices(medicine_names)
        
        return {
            "medicines_found": medicine_names,
            "results": comparison_results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing prescription: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
