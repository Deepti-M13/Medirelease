from typing import Dict, List, Optional

def analyze_negotiability(item: Dict) -> Dict:
    """
    Analyze a single item to determine negotiability and generating advice.
    
    Hard Rules for Logic:
    1. Life-saving/Critical items -> Not Negotiable (mostly).
    2. Medicines -> Negotiable (Generic check).
    3. Investigations -> Partially Negotiable.
    4. Room/Procedures -> Partially/Not Negotiable depending on context.
    """
    description = item.get('description', '').lower()
    category = item.get('category', '').lower()
    excess = item.get('excess', 0)
    
    # Defaults
    status = "Not negotiable"
    wording = "Charge appears standard for this facility."
    negotiable_amount = 0.0
    approach = "Billing Desk"
    
    # ---------------------------------------------------------
    # RULE 1: CRITICAL CARE / LIFE SAVING (Safety First)
    # ---------------------------------------------------------
    critical_keywords = [
        "icu", "ventilator", "oxygen", "emergency", "resuscitation",
        "adrenaline", "noradrenaline", "atropine", "dopamine", 
        "defibrillator", "intubation", "critical care"
    ]
    
    is_critical = any(keyword in description for keyword in critical_keywords)
    
    if is_critical:
        # Only negotiable if excess is extreme (> 5000 INR roughly, simplified logic)
        if excess > 5000:
            status = "Partially negotiable"
            negotiable_amount = excess * 0.5 # Conservative
            wording = (
                "While this is a critical care item, the cost seems unusually high. "
                "Politely ask for a detailed breakup to ensure no billing errors."
            )
            approach = "Medical Superintendent / Billing Manager"
        else:
            status = "Not negotiable"
            negotiable_amount = 0.0
            wording = "Critical care charge; usually strict norms apply. Best not to contest unless error is obvious."
            approach = "Billing Desk (for clarification only)"
            
        return {
            "status": status,
            "wording": wording,
            "amount": negotiable_amount,
            "approach": approach
        }

    # ---------------------------------------------------------
    # RULE 2: MEDICINES & CONSUMABLES (High Potential)
    # ---------------------------------------------------------
    if 'medicine' in category or 'pharmacy' in category:
        status = "Negotiable"
        negotiable_amount = excess
        wording = (
            "I noticed this brand is billed higher than standard market rates. "
            "Could we check if a generic equivalent or standard formulary price applies here?"
        )
        approach = "Pharmacy Manager / Billing Desk"
        return {
            "status": status,
            "wording": wording,
            "amount": negotiable_amount,
            "approach": approach
        }

    # ---------------------------------------------------------
    # RULE 3: INVESTIGATIONS / LAB (Medium Potential)
    # ---------------------------------------------------------
    if 'investigation' in category or 'lab' in category or 'pathology' in category:
        status = "Partially negotiable"
        negotiable_amount = excess * 0.75 # Often can get 10-20% discount, but here we cap excess claim
        wording = (
            "The lab charges seem above standard rates. "
            "Is it possible to review these against the hospital's standard tariff card?"
        )
        approach = "Lab In-charge / Billing Manager"
        return {
            "status": status,
            "wording": wording,
            "amount": negotiable_amount,
            "approach": approach
        }

    # ---------------------------------------------------------
    # RULE 4: ROOM CHARGES & NURSING (Context Dependent)
    # ---------------------------------------------------------
    if 'room' in category or 'bed' in category or 'nursing' in category:
        if excess > 0:
            status = "Partially negotiable"
            negotiable_amount = excess
            wording = (
                "I believe there might be an overlap in day calculation. "
                "Could you please verify the check-in and check-out timings?"
            )
            approach = "Admission/Billing Desk"
            return {
                "status": status,
                "wording": wording,
                "amount": negotiable_amount,
                "approach": approach
            }

    # ---------------------------------------------------------
    # RULE 5: PROCEDURES / SURGERIES (Package vs Itemized)
    # ---------------------------------------------------------
    if 'procedure' in category or 'surgery' in category or 'ot' in category:
        status = "Not negotiable" # Usually fixed packages
        negotiable_amount = 0.0
        wording = (
            "Procedure charges are typically fixed. "
            "However, if this was a package, please check if consumables were double-charged."
        )
        approach = "Billing Manager"
        # Exception: huge excess implies something wrong
        if excess > 10000:
             status = "Partially negotiable"
             negotiable_amount = excess * 0.3
             wording = "The procedure cost varies significantly from the estimate. Could I see the cost breakdown?"
        
        return {
            "status": status,
            "wording": wording,
            "amount": negotiable_amount,
            "approach": approach
        }

    # ---------------------------------------------------------
    # DEFAULT CATCH-ALL
    # ---------------------------------------------------------
    if excess > 0:
        status = "Partially negotiable"
        negotiable_amount = excess * 0.5
        wording = "This charge is unclear. Could you please provide an itemized explanation for this amount?"
        approach = "Billing Desk"
    else:
        status = "Not negotiable"
        negotiable_amount = 0.0
        wording = "Charge appears within expected range."
        approach = "None"

    return {
        "status": status,
        "wording": wording,
        "amount": negotiable_amount,
        "approach": approach
    }


def get_negotiation_suggestions(overcharged_items: list) -> list:
    """
    Process list of overcharged items and attach negotiation advice.
    """
    suggestions = []
    
    for item in overcharged_items:
        # Input safety
        if not item.get('description') or item.get('description') == 'UNKNOWN':
            continue
            
        analysis = analyze_negotiability(item)
        
        suggestion = {
            'item': item['description'],
            'excess_amount': item.get('excess', 0),
            'negotiable': analysis['status'],
            'suggested_wording': analysis['wording'],
            'potentially_negotiable_amount': analysis['amount'],
            'whom_to_approach': analysis['approach']
        }
        suggestions.append(suggestion)
    
    return suggestions


def generate_negotiation_summary(overcharged_items: list) -> Dict:
    """
    Generate a full summary including totals and advice list.
    """
    suggestions = get_negotiation_suggestions(overcharged_items)
    
    total_negotiable = sum(s['potentially_negotiable_amount'] for s in suggestions)
    total_excess = sum(s['excess_amount'] for s in suggestions)
    
    summary_text = (
        f"We identified ₹{total_negotiable:.2f} in potentially negotiable charges out of ₹{total_excess:.2f} excess. "
        "Focus on medicines and unexplained lab charges first."
    )
    
    if not suggestions:
        summary_text = "No significant negotiable items found. The bill appears largely consistent with standard protocols."

    return {
        'suggestions': suggestions,
        'total_overcharge': total_excess,
        'potentially_negotiable': total_negotiable,
        'summary': summary_text
    }
