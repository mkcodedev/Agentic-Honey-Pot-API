import requests
import time
import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/honeypot"
API_KEY = os.getenv("HONEYPOT_API_KEY")

def send_message(session_id, text, history):
    print(f"\n[SCAMMER]: {text}")
    print("[System]: Sending to Agent...")
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": text,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": history,
        "metadata": {"channel": "Demo", "language": "English", "locale": "IN"}
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers={"x-api-key": API_KEY}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[AGENT]: {data['reply']}")
            if data.get("scamDetected"):
                print("🚨 SCAM DETECTED!")
            
            # Update history
            history.append(payload["message"])
            history.append({
                "sender": "user",
                "text": data["reply"],
                "timestamp": int(time.time() * 1000)
            })
            
            if "intelligence" in data and data["intelligence"]:
                print(f"[INTEL]: {json.dumps(data['intelligence'], indent=2)}")
                
            return history
        else:
            print(f"Error: {response.text}")
            return history
    except Exception as e:
        print(f"Connection failed: {e}")
        return history

def run_demo():
    print("=== STARTING AUTOMATED DEMO ===")
    session_id = f"demo-{int(time.time())}"
    history = []
    
    scenarios = [
        "Hello, I am calling from your bank.",
        "Your account is blocked. Verify immediately.",
        "Please provide your UPI ID to unblock: scammer@upi",
        "Also need your PIN number to verify.",
        "Click this link: http://malicious-link.com",
        "If you don't do this, police will come.",
        "What is your OTP?",
        "Okay, I will send a QR code."
    ]
    
    for msg in scenarios:
        history = send_message(session_id, msg, history)
        time.sleep(1.5)
        
    print("\n=== DEMO COMPLETE ===")
    print("Run 'python simple_client.py' to chat manually.")

if __name__ == "__main__":
    run_demo()
