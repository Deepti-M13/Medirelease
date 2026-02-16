import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client with compatible version
groq_client = None
api_key = os.getenv("GROQ_API_KEY")

print(f"[DEBUG] Initializing Groq client...")
print(f"[DEBUG] API key present: {bool(api_key)}")

if api_key and api_key != "your_groq_api_key_here":
    try:
        print(f"[DEBUG] API key starts with: {api_key[:10]}...")
        # Initialize without problematic parameters for version 0.4.0
        groq_client = Groq(api_key=api_key)
        print("[SUCCESS] Groq client initialized successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Groq client: {e}")
        groq_client = None
else:
    print("[WARNING] No valid Groq API key found, will use fallback template")


def generate_discharge_summary(clinical_notes: str, patient_name: str = "") -> str:
    """
    Generate a discharge summary from clinical notes using Groq API
    
    Args:
        clinical_notes: Raw clinical notes from doctor
        patient_name: Patient name (optional)
    
    Returns:
        Structured discharge summary
    """
    if not groq_client:
        # Fallback if API key not configured
        print("[DEBUG] Using fallback summary (Groq client not initialized)")
        return generate_mock_summary(clinical_notes, patient_name)
    
    try:
        print("[DEBUG] Calling Groq API to generate discharge summary...")
        prompt = f"""You are a senior medical expert creating a FINAL discharge summary.
    
    CRITICAL INSTRUCTION:
    - You must STRICTLY apply all instructions found in the Clinical Notes.
    - If the notes specify a change (e.g., dosage increase, frequency change), it MUST override any standard protocol.
    - Doctor's instructions are mandatory and absolute.
    - Do NOT ignore any specific values (dosages, frequencies, timings) mentioned in the notes.

    Based on the following clinical notes, generate the discharge summary:

    Clinical Notes:
    {clinical_notes}

    Generate a structured discharge summary with the following sections:

    **DISCHARGE SUMMARY:**
    1. Patient Name: {patient_name if patient_name else '[To be filled]'}
    2. Diagnosis: [Primary and secondary diagnoses]
    3. Treatment Provided: [Detailed treatment administered]
    4. Current Condition: [Patient's condition at discharge]

    **MEDICATIONS PRESCRIBED:**
    List each medication with:
    - Medicine name
    - Dosage (e.g., 500mg)
    - Frequency (e.g., twice daily)
    - Timing (e.g., morning and evening after meals)
    - Duration (e.g., for 7 days)

    Example format:
    - Paracetamol 500mg - Take one tablet twice daily (morning and evening after meals) for 5 days
    - Omeprazole 20mg - Take one capsule once daily (morning before breakfast) for 14 days

    **FOLLOW-UP INSTRUCTIONS:**
    - When to schedule next appointment
    - What to monitor at home
    - When to remove stitches/dressings (if applicable)

    **DIET ADVICE:**
    - Specific dietary recommendations
    - Foods to avoid
    - Hydration advice

    **RED FLAG SYMPTOMS (When to seek immediate medical attention):**
    - Specific warning signs related to the condition
    - Emergency symptoms to watch for

    Keep it professional, detailed, and patient-friendly. Include specific timings for medications."""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior medical discharge summary generator. Your task is to generate the FINAL discharge summary by STRICTLY APPLYING the doctor's latest changes. Doctor changes are mandatory and must override any existing or standard information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1, # Lower temperature for strict adherence
            max_tokens=2000
        )
        
        summary = completion.choices[0].message.content
        print(f"[SUCCESS] Groq API call successful! Generated {len(summary)} characters")
        return summary
        
    except Exception as e:
        print(f"[ERROR] Error generating summary with Groq: {e}")
        print("[DEBUG] Falling back to template summary")
        return generate_mock_summary(clinical_notes, patient_name)


def parse_summary_sections(full_text: str) -> dict:
    """
    Parse the full AI-generated summary text into distinct sections
    to map to the database fields:
    - summary_text (General + Meds)
    - follow_up
    - diet_advice
    - red_flags
    """
    import re
    
    sections = {
        'summary_text': '',
        'follow_up': '',
        'diet_advice': '',
        'red_flags': ''
    }
    
    # regex patterns for our headers
    # Note: The prompt uses **HEADER:** format
    
    # We want to capture everything up to Follow-up as "summary_text"
    # Then separate the rest.
    
    # Split by known headers
    # We use a splitting strategy
    
    # Normalize newlines
    text = full_text.strip()
    
    # Define split markers
    markers = [
        (r'\*\*FOLLOW-UP INSTRUCTIONS:\*\*', 'follow_up'),
        (r'\*\*DIET ADVICE:\*\*', 'diet_advice'),
        (r'\*\*RED FLAG SYMPTOMS.*?\*\*', 'red_flags')
    ]
    
    # Find positions
    positions = []
    for pattern, key in markers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            positions.append((match.start(), key))
            
    # Sort by position
    positions.sort()
    
    if not positions:
        # No structure found, everything goes to summary_text
        sections['summary_text'] = text
        return sections
        
    # Main summary is everything before the first marker
    first_pos = positions[0][0]
    sections['summary_text'] = text[:first_pos].strip()
    
    # Loop through to get other sections
    for i, (pos, key) in enumerate(positions):
        # Start after the match
        # We need to find the end of the match (header)
        # Re-match to get the end
        pattern = next(m[0] for m in markers if m[1] == key)
        match = re.search(pattern, text[pos:], re.IGNORECASE)
        content_start = pos + match.end()
        
        # content ends at next marker or end of string
        if i + 1 < len(positions):
            content_end = positions[i+1][0]
        else:
            content_end = len(text)
            
        content = text[content_start:content_end].strip()
        sections[key] = content
        
    return sections


def generate_mock_summary(clinical_notes: str, patient_name: str = "") -> str:
    """Fallback mock summary generator"""
    return f"""DISCHARGE SUMMARY

Patient Name: {patient_name if patient_name else '[To be filled]'}

DIAGNOSIS:
Based on clinical evaluation and findings from the provided notes.

TREATMENT PROVIDED:
Treatment administered as per standard protocols and patient condition.

CURRENT CONDITION:
Patient's condition assessed and deemed stable for discharge.

MEDICATIONS PRESCRIBED:
[Please add medications with the following format]
- Medicine Name [Dosage] - Take [frequency] ([timing]) for [duration]

Example:
- Paracetamol 500mg - Take one tablet twice daily (morning and evening after meals) for 5 days
- Cefuroxime 500mg - Take one tablet twice daily (morning and evening) for 7 days

FOLLOW-UP INSTRUCTIONS:
- Schedule follow-up appointment within [X] days
- Monitor vital signs at home
- Return for suture removal if applicable

DIET ADVICE:
- Light, easily digestible food
- Adequate hydration (8-10 glasses of water daily)
- Avoid spicy and oily foods

RED FLAG SYMPTOMS:
⚠️ Seek immediate medical attention if you experience:
- High fever (>101°F)
- Severe pain not relieved by medication
- Any unusual bleeding or discharge
- Difficulty breathing
- Persistent vomiting

Clinical Notes Reference:
{clinical_notes[:200]}...

[Note: This is a template summary. Please edit and complete with actual patient-specific details.]
"""
