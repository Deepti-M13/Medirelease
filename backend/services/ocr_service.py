import pytesseract
from PIL import Image
import io
import re

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from an image using Tesseract OCR.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Use English language for now
        text = pytesseract.image_to_string(image, lang='eng')
        return text
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""

def clean_medicine_name(text: str) -> list[str]:
    """
    Cleans the OCR output to extract potential medicine names.
    Removes dosages, quantity instructions, and common noise.
    """
    lines = text.split('\n')
    extracted_names = []
    
    # Common words/units to filter out
    # Including instructions, headers, and noise identified by the user
    ignore_keywords = {
        'tablet', 'capsule', 'syrup', 'tab', 'cap', 'syr', 'injection', 'inj',
        'daily', 'od', 'bd', 'tds', 'tid', 'qid', 'hs', 'sos',
        'dr.', 'date', 'patient', 'prescription', 'name', 'age', 'sex', 'weight',
        'history', 'diagnosis', 'investigations', 'qualification', 'advice',
        'follow', 'instructions', 'available', 'buy', 'price', 'online', 'pharmacy',
        'after', 'before', 'food', 'stomach', 'morning', 'night', 'day', 'water',
        'drink', 'plenty', 'fluids', 'rest', 'adequate', 'take', 'give', 'apply',
        'use', 'for', 'reg', 'medicine', 'medication', 'prescribed', 'clinic', 'hospital',
        'pharmeasy', 'tata', '1mg', 'netmeds', 'apollo', 'generic', 'brand', 'order',
        'delivery', 'cart', 'checkout', 'items', 'total', 'mrp'
    }
    
    ignore_patterns = [
        r'\d+mg', r'\d+g', r'\d+ml', r'\d+%', r'x\s*\d+', r'\d+\s*days?', r'\d+\s*weeks?'
    ]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3: 
            continue
            
        # Basic cleaning: Remove special chars/numbers at start
        cleaned_line = re.sub(r'^[\d\W]+', '', line)
        
        # Heuristic: If line looks like a header or irrelevant, skip
        lower_line = cleaned_line.lower()
        if any(keyword in lower_line for keyword in ['doctor', 'hospital', 'clinic', 'registration']):
            continue

        # Extract only the name part (usually before the dosage)
        # capture name before first number (often dosage)
        match = re.search(r'^([a-zA-Z\s\-]+)', cleaned_line)
        if match:
            candidate = match.group(1).strip()
            
            # Filter against regex patterns (like dosages)
            if any(re.search(pattern, candidate, re.IGNORECASE) for pattern in ignore_patterns):
                continue

            # Split candidate into words
            words = candidate.split()
            cleaned_words = []
            
            for word in words:
                if word.lower() not in ignore_keywords:
                    cleaned_words.append(word)
            
            if cleaned_words:
                final_name = " ".join(cleaned_words).strip()
                if len(final_name) > 2:
                    extracted_names.append(final_name.title())
        else:
            # Fallback: take the whole line if it's purely letters/spaces
             if re.match(r'^[a-zA-Z\s\-]+$', cleaned_line):
                 candidate = cleaned_line.strip()
                 words = candidate.split()
                 cleaned_words = [w for w in words if w.lower() not in ignore_keywords]
                 if cleaned_words:
                    final_name = " ".join(cleaned_words).strip()
                    if len(final_name) > 2:
                        extracted_names.append(final_name.title())

    # Return unique names (case-insensitive deduplication via titling)
    unique_names = sorted(list(set(extracted_names)))
    return unique_names
