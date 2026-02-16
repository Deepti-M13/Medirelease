import os
import csv
import re
from typing import List, Dict

# Load medicine mapping data
MEDICINE_MAPPING = {}
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def load_medicine_mapping():
    """Load brand-to-generic medicine mapping from CSV"""
    global MEDICINE_MAPPING
    try:
        csv_path = os.path.join(DATA_DIR, 'medicine_mapping.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row['brand_name'].lower()
                MEDICINE_MAPPING[brand] = {
                    'generic_name': row['generic_name'],
                    'expected_price': float(row['expected_price_per_unit']),
                    'unit': row['unit']
                }
    except Exception as e:
        print(f"Warning: Could not load medicine mapping: {e}")


def extract_medicine_names(text: str) -> List[str]:
    """
    Extract medicine names from bill text
    
    This is a simplified implementation. In production, you'd use:
    - Medical NER (Named Entity Recognition)
    - Drug name databases
    - More sophisticated pattern matching
    """
    medicines = []
    
    # Common medicine indicators
    medicine_patterns = [
        r'(Tab|Cap|Inj|Syr)\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:ol|in|ex|one|ide|ate|ine))\s+\d+\s*mg',
    ]
    
    for pattern in medicine_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                medicine_name = ' '.join(match).strip()
            else:
                medicine_name = match.strip()
            
            if medicine_name and len(medicine_name) > 2:
                medicines.append(medicine_name)
    
    return list(set(medicines))  # Remove duplicates


def analyze_medicine_prices(bill_text: str, categorized_medicines: List[Dict]) -> List[Dict]:
    """
    Analyze medicine prices by mapping brands to generics and comparing prices
    
    Args:
        bill_text: Extracted text from bill
        categorized_medicines: List of medicine items from bill categorization
    
    Returns:
        List of medicine analyses with brand, generic, and price comparison
    """
    if not MEDICINE_MAPPING:
        load_medicine_mapping()
    
    analyses = []
    
    # Extract medicine names
    medicine_names = extract_medicine_names(bill_text)
    
    # Also use categorized medicines
    for med_item in categorized_medicines:
        desc = med_item['description']
        billed_price = med_item['amount']
        
        # Try to find brand in mapping
        brand_found = None
        generic_info = None
        
        for brand, info in MEDICINE_MAPPING.items():
            if brand in desc.lower():
                brand_found = brand
                generic_info = info
                break
        
        if generic_info:
            expected_price = generic_info['expected_price']
            excess = billed_price - expected_price
            
            analyses.append({
                'brand_name': brand_found.title(),
                'generic_name': generic_info['generic_name'],
                'billed_price': billed_price,
                'expected_price': expected_price,
                'excess': excess,
                'unit': generic_info['unit']
            })
        else:
            # No mapping found, use fallback
            # Estimate: assume 30-50% markup is common
            estimated_generic_price = billed_price * 0.6
            
            analyses.append({
                'brand_name': desc[:50],
                'generic_name': 'Generic equivalent not found',
                'billed_price': billed_price,
                'expected_price': estimated_generic_price,
                'excess': billed_price - estimated_generic_price,
                'unit': 'estimated',
                'note': 'Price estimate based on typical brand markup'
            })
    
    return analyses


def get_total_medicine_excess(analyses: List[Dict]) -> float:
    """Calculate total excess amount spent on medicines"""
    return sum(item['excess'] for item in analyses if item['excess'] > 0)
