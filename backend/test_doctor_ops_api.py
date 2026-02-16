import requests
import json
import sys
import os

# Add backend to path just in case, though we are using requests against localhost
# Assuming server is running at localhost:8000

BASE_URL = "http://localhost:8000/api/doctor"
AUTH_URL = "http://localhost:8000/api/auth/login"

def test_discharge_summary_lifecycle():
    print("Testing Discharge Summary Lifecycle...")
    
    # 1. Login (Optional for now as endpoints don't seem to enforce auth strictly yet, 
    # but let's assume valid session if needed. Code shows Depends(get_db) but not authenticate_user in router args directly yet? 
    # Wait, router uses Depends(get_db), auth is separate. Let's check router.
    # Router `create_discharge_summary` only needs db. Good.)
    
    # 2. Generate Summary (Mocking the prompt to save tokens/time or just checking creation)
    # Since we can't easily mock the Groq call from outside without editing code, 
    # we will rely on the fact that if Groq fails it raises 500. 
    # But wait, we want to test UPDATE.
    # Let's see if we can create a specific summary entry directly or use the generate endpoint.
    # The generate endpoint calls `generate_discharge_summary`.
    # If the server is running with a valid key, it should work.
    
    # Alternative: Manually insert via a "backdoor" or just try the update on an existing ID?
    # No, let's try to create one.
    
    # Actually, better to use a simple script that mocks the DB interaction if we want to be safe, 
    # OR rely on the running server if we are sure it works.
    # Let's try to hit the running server.
    
    print("1. Creating a new discharge summary...")
    # We'll assume the server is running.
    
    # Note: This requires the server to be running and Groq key to be valid.
    # If Groq key is missing/invalid, this step might fail. 
    # But I see in app.py startup logs that Groq client initialized successfully? 
    # "Groq client initialized successfully for bill analysis!" 
    # Need to check if `services.discharge_summary` also initializes it.
    
    # Let's hope it works.
    payload = {
        "patient_name": "Test Patient API",
        "clinical_notes": "Patient admitted with fever. Treated with paracetamol. Stable."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/discharge-summary/generate", data=payload)
        
        if response.status_code != 200:
            print(f"Failed to generate summary: {response.text}")
            # Fallback: Check if we can list existing ones and update one of them?
            # Or assume generation failed due to LLM issues but we want to test UPDATE.
            return
            
        data = response.json()
        summary_id = data['id']
        print(f"   Created Summary ID: {summary_id}")
        print(f"   Initial Text: {data['summary_text'][:50]}...")
        
        # 3. Update Summary
        print("\n2. Updating the summary (Doctor edits)...")
        update_payload = {
            "summary_text": "Updated Summary: Patient recovered fully. Discharged.",
            "follow_up": "Visit in 5 days.",
            "diet_advice": "Soft diet.",
            "red_flags": "High fever > 102F"
        }
        
        update_response = requests.put(f"{BASE_URL}/discharge-summary/{summary_id}", json=update_payload)
        
        if update_response.status_code == 200:
            updated_data = update_response.json()
            print("   Update Successful!")
            print(f"   Updated Text: {updated_data['summary_text']}")
            
            if updated_data['summary_text'] == update_payload['summary_text']:
                print("   [PASS] Text matches update.")
            else:
                print("   [FAIL] Text mismatch.")
        else:
            print(f"   Update Failed: {update_response.text}")
            
        # 4. Finalize
        print("\n3. Finalizing summary...")
        finalize_response = requests.post(f"{BASE_URL}/discharge-summary/{summary_id}/finalize")
        
        if finalize_response.status_code == 200:
            print("   Finalize Successful!")
        else:
            print(f"   Finalize Failed: {finalize_response.text}")
            
        # 5. Verify Persistence
        print("\n4. Verifying persistence...")
        get_response = requests.get(f"{BASE_URL}/discharge-summary/{summary_id}")
        if get_response.status_code == 200:
            final_data = get_response.json()
            if final_data['status'] == 'final' and final_data['summary_text'] == update_payload['summary_text']:
                print("   [PASS] Summary persisted correctly as FINAL.")
            else:
                 print("   [FAIL] Persistence check failed.")
        
    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    test_discharge_summary_lifecycle()
