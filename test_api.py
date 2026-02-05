"""
Test script to verify the honeypot API
Run this after starting the server to test basic functionality
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"  # Change this to match your .env

def test_health_check():
    """Test the health endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_honeypot_scam_detection():
    """Test the honeypot endpoint with a scam message"""
    print("🍯 Testing scam detection...")
    
    payload = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your account has been suspended. Verify immediately by sending OTP to +919876543210",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_multi_turn_conversation():
    """Test multi-turn conversation with intelligence extraction"""
    print("💬 Testing multi-turn conversation...")
    
    session_id = f"test-session-{int(time.time())}"
    
    messages = [
        "Hello, this is from your bank.",
        "Your account shows suspicious activity. We need to verify.",
        "Please provide your UPI ID for verification.",
        "Also share your account number: it should be 12 digits.",
        "The verification link is http://fake-bank.com/verify - click it now.",
        "This is urgent! Your account will be blocked in 1 hour.",
        "Please send the OTP you receive to this number: +919876543210",
        "Confirm your details: Account 123456789012, UPI: user@paytm"
    ]
    
    conversation_history = []
    
    for i, scammer_message in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"Scammer: {scammer_message}")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": scammer_message,
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/honeypot",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Agent: {result['reply']}")
            print(f"Scam Detected: {result['scamDetected']}")
            
            # Update conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": scammer_message,
                "timestamp": payload["message"]["timestamp"]
            })
            conversation_history.append({
                "sender": "user",
                "text": result['reply'],
                "timestamp": payload["message"]["timestamp"] + 1
            })
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            break
        
        # Small delay between messages
        time.sleep(0.5)
    
    print("\n✅ Multi-turn conversation test completed!")
    print(f"Total messages: {len(messages)}")

def test_invalid_api_key():
    """Test with invalid API key"""
    print("🔒 Testing invalid API key...")
    
    payload = {
        "sessionId": "test-session-invalid",
        "message": {
            "sender": "scammer",
            "text": "Test message",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    headers = {
        "x-api-key": "wrong-api-key",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("  Agentic Honey-Pot API Test Suite")
    print("=" * 50)
    print()
    
    try:
        # Run tests
        test_health_check()
        test_honeypot_scam_detection()
        test_invalid_api_key()
        test_multi_turn_conversation()
        
        print("\n" + "=" * 50)
        print("  ✅ All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        print("Make sure the server is running at", BASE_URL)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
