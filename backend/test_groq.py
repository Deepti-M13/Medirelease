import os
from dotenv import load_dotenv
import sys

# Load env vars
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

print(f"Python version: {sys.version}")
print(f"API Key found: {bool(api_key)}")
if api_key:
    print(f"API Key prefix: {api_key[:10]}...")

try:
    import groq
    print(f"Groq module found. Version: {getattr(groq, '__version__', 'unknown')}")
    
    from groq import Groq
    
    print("Attempting to initialize Groq client...")
    client = Groq(api_key=api_key)
    print("Groq client initialized successfully!")
    
    print("Attempting simple chat completion...")
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Say hello"}
        ],
        max_tokens=10
    )
    print("Completion success!")
    print(f"Response: {completion.choices[0].message.content}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
