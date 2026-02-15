"""
Scam detection module
Implements Hybrid: Keyword + Apriori Confidence Model
"""
import re
from typing import List, Tuple
from models import Message

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
    }
    
    for keyword, weight in HIGH_RISK_KEYWORDS.items():
        if keyword in all_text:
            score += weight
            detected_keywords.append(keyword)
    
    # Pattern-based rules (Apriori-like)
    patterns = [
        (["urgent", "verify"], 0.3),
        (["account", "blocked"], 0.35),
        (["account", "freeze"], 0.35),
        (["click", "link"], 0.25),
        (["otp", "verify"], 0.4),
        (["bank", "blocked"], 0.3),
        (["immediately", "verify"], 0.3),
        (["expire", "update"], 0.25),
    ]
    
    for pattern_words, pattern_weight in patterns:
        if all(word in all_text for word in pattern_words):
            score += pattern_weight
    
    # URL detection
    if "http://" in all_text or "https://" in all_text or ".com" in all_text:
        score += 0.15
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

def analyze_message(message: Message, conversation_history: List[Message], current_score: float = 0.0) -> Tuple[float, str, List[str]]:
    """
    Adapter function to maintain backward compatibility with main.py if needed,
    or we can update main.py to use calculate_confidence_score directly.
    """
    # Convert Message objects to dicts for the new function
    history_dicts = []
    for msg in conversation_history:
        history_dicts.append({"sender": msg.sender, "text": msg.text, "timestamp": msg.timestamp})
        
    new_score, keywords = calculate_confidence_score(message.text, history_dicts)
    
    # Max with current score to allow escalation
    final_score = max(new_score, current_score)
    
    classification, _ = classify_threat_level(final_score)
    
    return final_score, classification, keywords
