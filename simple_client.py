import requests
import uuid
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/honeypot"
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_honeypot_live_a8f92c3e4b5d6789xyz")

def print_separator():
    print("-" * 50)

def main():
    print_separator()
    print("AGENTIC HONEY-POT TERMINAL CLIENT")
    print_separator()
    
    # Initialize session
    session_id = f"session-{uuid.uuid4().hex[:12]}"
    conversation_history = []
    
    print(f"Session ID: {session_id}")
    print("Type 'quit' or 'exit' to stop.")
    print_separator()
    
    while True:
        # Get user input (simulating scammer)
        try:
            user_input = input("\n[SCAMMER]: ")
        except EOFError:
            break
            
        if user_input.lower() in ["quit", "exit"]:
            print("Ending session.")
            break
            
        if not user_input.strip():
            continue
            
        # Prepare request payload
        current_timestamp = int(time.time() * 1000)
        message = {
            "sender": "scammer",
            "text": user_input,
            "timestamp": current_timestamp
        }
        
        payload = {
            "sessionId": session_id,
            "message": message,
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "Terminal",
                "language": "English",
                "locale": "IN"
            }
        }
        
        # Send request
        print("[System]: Sending to Agentic AI...")
        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data["reply"]
                scam_detected = data.get("scamDetected", False)
                
                # Print response
                print(f"\n[AGENT]: {reply}")
                
                if scam_detected:
                    print(f"\n[System]: 🚨 SCAM DETECTED!")
                    
                # Update history
                conversation_history.append(message)
                conversation_history.append({
                    "sender": "user",  # Agent is 'user' in this context logic (victim)
                    "text": reply,
                    "timestamp": current_timestamp + 1000
                })
                
                # Show intelligence if present
                if "intelligence" in data and data["intelligence"]:
                    intel = data["intelligence"]
                    found = []
                    for k, v in intel.items():
                        if v: found.append(f"{k}: {v}")
                    if found:
                        print(f"[System]: Intelligence Extracted: {', '.join(found)}")
                        
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Connection Error: {e}")
            print("Make sure the backend is running: uvicorn main:app --reload")

if __name__ == "__main__":
    main()
