"""
Scam detection module
Implements Hybrid: Keyword + Apriori Confidence Model
"""
import re
from typing import List, Tuple
from src.models import Message

def calculate_confidence_score(message_text: str, conversation_history: List[dict]) -> Tuple[float, List[str]]:
    """
    Calculate scam confidence score using Apriori-like pattern detection
    Score: 0.0 to 1.0
    - 0.0 to 0.3 = Genuine
    - 0.3 to 0.7 = Suspicious  
    - 0.7 to 1.0 = Scammer
    """
    
    score = 0.0
    detected_keywords = []
    
    # Combine current message and history
    all_text = message_text.lower()
    for msg in conversation_history:
        # Support both Dict and Message object input
        if isinstance(msg, dict):
            if msg.get("sender") == "scammer":
                all_text += " " + msg.get("text", "").lower()
        else: # Access as object attribute
            if msg.sender == "scammer":
                all_text += " " + msg.text.lower()
    
    # Keyword scoring (weighted)
    HIGH_RISK_KEYWORDS = {
        "account": 0.15,
        "blocked": 0.2,
        "freeze": 0.2,
        "freezed": 0.2,
        "suspend": 0.2,
        "verify": 0.15,
        "urgent": 0.15,
        "immediately": 0.15,
        "otp": 0.25,
        "cvv": 0.3,
        "pin": 0.25,
        "password": 0.25,
        "expire": 0.2,
        "click": 0.1,
        "link": 0.1,
        "update": 0.1,
        "kyc": 0.2,
        "rbi": 0.15,
        "bank": 0.1,
        "debit": 0.1,
        "credit": 0.1,
        "cashback": 0.4,
        "won": 0.3,
        "prize": 0.3,
        "claim": 0.25,
        "iphone": 0.3,
        "offer": 0.2,
        "selected": 0.2,
        "paytm": 0.2,
        "phonepe": 0.2,
        "sbi": 0.25,
        "hdfc": 0.2,
        "icici": 0.2,
        "axis": 0.2,
        "compromised": 0.35,
        "kyc": 0.3,
        "pan": 0.25,
        "aadhar": 0.25,
    }
    
    for keyword, weight in HIGH_RISK_KEYWORDS.items():
        if keyword in all_text:
            score += weight
            detected_keywords.append(keyword)
    
    # Pattern-based rules (Apriori-like)
    patterns = [
        (["urgent", "verify"], 0.3),
        (["account", "blocked"], 0.4),
        (["account", "freeze"], 0.4),
        (["click", "link"], 0.3),
        (["otp", "verify"], 0.4),
        (["bank", "blocked"], 0.35),
        (["immediately", "verify"], 0.3),
        (["expire", "update"], 0.3),
        (["cashback", "won"], 0.5),
        (["claim", "reward"], 0.4),
        (["selected", "iphone"], 0.45),
        (["offer", "expires"], 0.3),
        (["sbi", "blocked"], 0.5),
        (["compromised", "account"], 0.5),
    ]
    
    for pattern_words, pattern_weight in patterns:
        if all(word in all_text for word in pattern_words):
            score += pattern_weight
    
    # URL detection
    if "http://" in all_text or "https://" in all_text or ".com" in all_text:
        score += 0.25
        detected_keywords.append("URL detected")
    
    # Cap score at 1.0
    score = min(score, 1.0)
    
    return round(score, 2), list(set(detected_keywords))


def classify_threat_level(confidence_score: float) -> Tuple[str, str]:
    """
    Classify based on confidence score
    Returns: (Classification, Emoji)
    """
    if confidence_score >= 0.87:
        return "scammer", "🔴"
    elif confidence_score >= 0.3:
        return "suspicious", "🟡"
    else:
        return "genuine", "🟢"

def is_scam(message: Message, conversation_history: List[Message], current_score: float = 0.0) -> Tuple[bool, List[str]]:
    """
    Analyzes a message to determine if it's a scam.
    Returns a boolean for scam detection and a list of detected keywords.
    """
    # Convert Message objects to dicts for the new function
    history_dicts = []
    for msg in conversation_history:
        history_dicts.append({"sender": msg.sender, "text": msg.text, "timestamp": msg.timestamp})
        
    new_score, keywords = calculate_confidence_score(message.text, history_dicts)
    
    # Max with current score to allow escalation
    final_score = max(new_score, current_score)
    
    classification, _ = classify_threat_level(final_score)
    
    # The main application expects a boolean for scam_detected
    scam_detected = classification in ["scammer", "suspicious"]
    
    return scam_detected, keywords
