"""
Scam detection module
Implements keyword-based and optional LLM-based scam detection
"""
import os
import re
from typing import List, Tuple
from models import Message

# Common scam keywords and patterns
SCAM_KEYWORDS = [
    # Urgency keywords
    "urgent", "immediately", "asap", "right now", "today only", "limited time",
    "expire", "expires", "expired", "deadline", "last chance",
    
    # Account/verification keywords
    "verify", "verification", "confirm", "suspended", "blocked", "locked",
    "deactivated", "disabled", "frozen", "restricted", "limited",
    
    # Financial keywords
    "upi", "bank account", "credit card", "debit card", "atm", "pin",
    "cvv", "otp", "one time password", "transaction", "payment",
    "refund", "cashback", "reward", "prize", "won", "winner",
    
    # Authority impersonation
    "rbi", "reserve bank", "income tax", "tax department", "police",
    "government", "official", "ministry", "customs", "irs",
    
    # Action requests
    "click here", "update now", "verify now", "call us", "contact us",
    "send money", "transfer", "deposit", "pay now", "submit",
    
    # Threats
    "legal action", "arrest", "warrant", "penalty", "fine", "sue",
    "court", "investigation", "fraud case", "complaint",
    
    # Common scam phrases
    "congratulations", "you have won", "claim now", "free gift",
    "selected customer", "lucky draw", "lottery"
]


def detect_scam_keywords(text: str) -> Tuple[bool, List[str]]:
    """
    Detect scam using keyword matching
    
    Args:
        text: Message text to analyze
        
    Returns:
        Tuple of (is_scam, found_keywords)
    """
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in SCAM_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Consider it a scam if 2+ keywords found
    is_scam = len(found_keywords) >= 2
    
    return is_scam, found_keywords


def detect_suspicious_patterns(text: str) -> Tuple[bool, List[str]]:
    """
    Detect suspicious patterns like account numbers, URLs, etc.
    
    Args:
        text: Message text to analyze
        
    Returns:
        Tuple of (has_suspicious_patterns, pattern_types)
    """
    patterns_found = []
    
    # Check for bank account numbers (9-18 digits)
    if re.search(r'\b\d{9,18}\b', text):
        patterns_found.append("bank_account")
    
    # Check for UPI IDs
    if re.search(r'\b[\w\.-]+@[\w\.-]+\b', text) and any(upi in text.lower() for upi in ['upi', '@paytm', '@phonepe', '@googlepay', '@ybl']):
        patterns_found.append("upi_id")
    
    # Check for URLs
    if re.search(r'https?://\S+', text) or re.search(r'www\.\S+', text):
        patterns_found.append("url")
    
    # Check for phone numbers
    if re.search(r'(\+91[\s-]?)?[6-9]\d{9}', text):
        patterns_found.append("phone_number")
    
    return len(patterns_found) > 0, patterns_found


def detect_scam_llm(text: str, conversation_history: List[Message]) -> Tuple[bool, str]:
    """
    Optional LLM-based scam detection using Google Gemini (via REST API)
    
    Args:
        text: Current message text
        conversation_history: Previous messages
        
    Returns:
        Tuple of (is_scam, reasoning)
    """
    llm_provider = os.getenv("LLM_PROVIDER", "").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")
    
    if llm_provider != "gemini" or not llm_api_key:
        return False, "LLM not configured"
    
    try:
        import requests
        import json
        
        # Use Gemini 1.5 Flash for speed and lower latency
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={llm_api_key}"
        
        # Build context from conversation history
        context = "\n".join([f"{msg.sender}: {msg.text}" for msg in conversation_history[-5:]])
        
        prompt = f"""You are a scam detection AI. Analyze the following message and conversation context.

Conversation Context:
{context}

Current Message:
{text}

Is this a scam attempt? Consider:
- Urgency tactics
- Requests for sensitive information (OTP, PIN, account details)
- Impersonation of authority (bank, government, police)
- Promises of prizes or refunds
- Threats of account suspension or legal action
- Suspicious links or payment requests

Respond with ONLY "YES" or "NO" followed by a brief reason.
Format: YES|<reason> or NO|<reason>"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code != 200:
            print(f"Gemini API Error in detection: {response.status_code} - {response.text}")
            return False, f"API Error: {response.status_code}"
            
        result = response.json()
        if 'candidates' not in result or not result['candidates']:
             return False, "No response from LLM"
             
        response_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        if response_text.startswith("YES"):
            return True, response_text.split("|", 1)[1] if "|" in response_text else "LLM detected scam"
        else:
            return False, response_text.split("|", 1)[1] if "|" in response_text else "Not a scam"
            
    except Exception as e:
        print(f"LLM detection error: {e}")
        return False, f"Error: {str(e)}"


def is_scam(message: Message, conversation_history: List[Message]) -> Tuple[bool, List[str]]:
    """
    Main scam detection function combining multiple detection methods
    
    Args:
        message: Current message to analyze
        conversation_history: Previous messages in the conversation
        
    Returns:
        Tuple of (is_scam, detected_keywords)
    """
    text = message.text
    
    # Keyword-based detection
    keyword_scam, keywords = detect_scam_keywords(text)
    
    # Pattern-based detection
    pattern_scam, patterns = detect_suspicious_patterns(text)
    
    # Combined decision: scam if keywords OR suspicious patterns detected
    is_scam_detected = keyword_scam or pattern_scam
    
    # Optional: Use LLM for additional verification if configured
    if os.getenv("LLM_PROVIDER") == "gemini" and not is_scam_detected:
        llm_scam, reasoning = detect_scam_llm(text, conversation_history)
        if llm_scam:
            is_scam_detected = True
            keywords.append(f"llm_detection: {reasoning}")
    
    return is_scam_detected, keywords
