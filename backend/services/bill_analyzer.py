import os
import json
import csv
import pytesseract
from PIL import Image
import pdfplumber
from typing import Dict, List, Tuple
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configure Tesseract path for Windows
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', ''))
]

for path in TESSERACT_PATHS:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        print(f"[DEBUG] Tesseract found at: {path}")
        break
else:
    print("[WARNING] Tesseract OCR not found in common paths. Bill image analysis may fail.")
    print("[INFO] Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")

# Initialize Groq client
groq_client = None
api_key = os.getenv("GROQ_API_KEY")

if api_key and api_key != "your_groq_api_key_here":
    try:
        groq_client = Groq(api_key=api_key)
        print("[SUCCESS] Groq client initialized successfully for bill analysis!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Groq client: {e}")
else:
    print("[WARNING] No valid Groq API key found. Bill analysis will fail or use mock data.")

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_reference_data() -> str:
    """Load reference data (CGHS rates and Medicine mapping) to context string"""
    context = "REFERENCE PRICING DATA:\n\n"
    
    try:
        # Load CGHS Rates
        cghs_path = os.path.join(DATA_DIR, 'cghs_rates.csv')
        if os.path.exists(cghs_path):
            context += "CGHS RATES (Standard Government Rates):\n"
            with open(cghs_path, 'r', encoding='utf-8') as f:
                context += f.read()
            context += "\n\n"
            
        # Load Medicine Mapping
        med_path = os.path.join(DATA_DIR, 'medicine_mapping.csv')
        if os.path.exists(med_path):
            context += "MEDICINE MAPPING (Brand -> Generic & Expected Price):\n"
            with open(med_path, 'r', encoding='utf-8') as f:
                context += f.read()
            context += "\n\n"
            
    except Exception as e:
        print(f"Error loading reference data: {e}")
        
    return context

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from image or PDF bill
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            image = Image.open(file_path)
            # Use specific config for billing documents if needed, but default is usually okay
            text = pytesseract.image_to_string(image)
            return text
            
        elif ext == '.pdf':
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
            
        else:
            return ""
            
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def analyze_bill_with_llm(text: str) -> Dict:
    """
    Analyze bill text using Groq LLM to identify overcharged items
    """
    if not groq_client:
        return {"error": "LLM client not available"}

    reference_data = load_reference_data()
    
    prompt = f"""You are an expert AI medical bill auditor. Your task is to analyze the extracted text from a hospital or pharmacy bill and identify GENUINELY OVERPRICED charges.

INPUT CONTEXT:
1. RAW BILL TEXT (may contain OCR errors):
\"\"\"
{text}
\"\"\"

2. REFERENCE DATA (Use this for price comparisons):
\"\"\"
{reference_data}
\"\"\"

ANALYSIS LOGIC:
1. **Identify Items**: Parse medicines, investigations, room charges, etc.
2. **Correct OCR**: Fix obvious typos (e.g., '10000' appearing as '10,000' is fine, but '10.00' as '1000' needs context).
3. **Determine Expected Price**: 
   - Check the REFERENCE DATA first.
   - If not found, use your internal knowledge of GENERIC medicine prices and standard hospital rates in India (INR).
   - Assume standard hospital markup (20-30% over pharmacy price is fair).
4. **Compare & Calculate Excess**:
   - Billed Amount vs Expected Amount.
   - **HARD RULE**: Mark as 'Fairly Charged' if the difference is < 20% or if the amount is trivial.
   - **HARD RULE**: Only flag as 'Overcharged' if the excess is significant.

OUTPUT JSON FORMAT (Strictly follow this):
{{
  "summary": "Brief analysis summary (1-2 sentences)",
  "total_billed_amount": <float>,
  "total_expected_amount": <float>,
  "total_overcharged_amount": <float>,
  "items": [
    {{
      "name": "Item Description",
      "category": "Medicine|Investigation|Room|Procedure|Other",
      "quantity": <int/float>,
      "billed_price": <float>,
      "expected_price": <float>,
      "excess_amount": <float>,
      "status": "Overcharged|Fair",
      "reason": "Why it is fair or overcharged (mention generic equivalent if applicable)"
    }}
  ]
}}

Return ONLY the valid JSON string. No markdown formatting.
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a precise medical data analyst. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        return json.loads(response_content)
        
    except Exception as e:
        print(f"[ERROR] LLM analysis failed: {e}")
        return {"error": str(e)}

def analyze_bill(file_path: str) -> Dict:
    """
    Main bill analysis function
    """
    # Extract text
    extracted_text = extract_text_from_file(file_path)
    
    if not extracted_text:
        return {
            'error': 'Could not extract text from bill',
            'extracted_text': '',
            'analysis': None
        }
    
    # Analyze with LLM
    analysis_result = analyze_bill_with_llm(extracted_text)
    
    return {
        'extracted_text': extracted_text,
        'analysis': analysis_result
    }

if __name__ == "__main__":
    # Test block
    print("Testing bill analysis...")
    # Add a dummy file path if you want to test locally, or rely on external calls

