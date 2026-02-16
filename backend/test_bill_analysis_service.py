import os
import sys
import json
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.bill_analyzer import analyze_bill_with_llm

def test_analysis():
    print("Testing Bill Analysis with LLM...")
    
    # Mock bill text with one overpriced item and one fair item
    mock_bill_text = """
    HOSPITAL INVOICE
    ----------------
    Patient: John Doe
    Date: 28-Jan-2025
    
    1. Consultation - Dr. Smith     ₹500.00
    2. Vitamin D3 Sachet            ₹250.00  (Expected ~₹40-50)
    3. Paracetamol 500mg (10 tabs)  ₹150.00  (Market price ~₹10-20)
    4. CBC Test                     ₹250.00
    
    Total: ₹1150.00
    """
    
    print(f"\n--- Input Bill Text ---\n{mock_bill_text}\n-----------------------")
    
    result = analyze_bill_with_llm(mock_bill_text)
    
    print("\n--- Analysis Result (JSON) ---")
    print(json.dumps(result, indent=2))
    
    # Simple validation
    if "error" in result:
        print("\n[FAIL] Analysis returned an error.")
    elif "items" in result:
        overcharged = [i for i in result['items'] if i['status'] == 'Overcharged']
        print(f"\n[SUCCESS] Analysis completed. Found {len(overcharged)} overcharged items.")
        
        # Check expected logic
        para_item = next((i for i in result['items'] if 'Paracetamol' in i['name']), None)
        if para_item and para_item['status'] == 'Overcharged':
            print("Logic Check 1: Paracetamol correctly flagged as Overcharged.")
        else:
            print("Logic Check 1: [WARNING] Paracetamol NOT flagged as Overcharged.")
            
    else:
        print("\n[FAIL] Unexpected response format.")

if __name__ == "__main__":
    test_analysis()
