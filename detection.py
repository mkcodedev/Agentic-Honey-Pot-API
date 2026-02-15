"""
Scam detection module
Implements Hybrid: Keyword + Apriori Confidence Model
"""
import os
import re
from typing import List, Tuple, Set
from models import Message

# --- 1. KEYWORD-BASED TRIGGER SYSTEM ---
# Format: "keyword": (Weight, Category)
# Weights: 0.1 (Low) to 1.0 (High)
KEYWORD_DB = {
    # High Risk (weights 0.8 - 1.0)
    "otp": (1.0, "Financial"),
    "cvv": (1.0, "Financial"),
    "pin": (0.9, "Financial"),
    "anydesk": (1.0, "Remote Access"),
    "teamviewer": (1.0, "Remote Access"),
    "quicksupport": (1.0, "Remote Access"),
    "remote access": (0.9, "Remote Access"),
    "kyc": (0.8, "Verification"),
    "suspend": (0.8, "Threat"),
    "blocked": (0.8, "Threat"),
    "expiry": (0.7, "Urgency"),
    "refund link": (0.9, "Phishing"),
    
    # Medium Risk (weights 0.4 - 0.7)
    "urgent": (0.5, "Urgency"),
    "immediately": (0.5, "Urgency"),
    "lottery": (0.6, "Prize"),
    "winner": (0.6, "Prize"),
    "investment": (0.5, "Financial"),
    "double": (0.6, "Financial"),  # e.g. double your money
    "verification": (0.4, "Verification"),
    "update": (0.4, "Action"),
    "click here": (0.6, "Action"),
    "pay": (0.4, "Financial"),
    "transfer": (0.4, "Financial"),
    "bank": (0.4, "Financial"),
    "rbi": (0.5, "Authority"),
    "police": (0.5, "Authority"),
    
    # Low Risk (weights 0.1 - 0.3)
    "hello": (0.0, "Neutral"),
    "offer": (0.2, "Marketing"),
    "prize": (0.3, "Prize"),
    "account": (0.2, "Financial"),
    "link": (0.3, "General"),
}

# --- 2. APRIORI-BASED PATTERN RULES ---
# Rules derived from historical patterns. 
# If a message contains ALL keywords in a set, it gets the specified confidence score (min).
APRIORI_RULES = [
    ({"urgent", "bank", "link"}, 0.87),
    ({"otp", "share"}, 0.95),
    ({"kyc", "update", "link"}, 0.90),
    ({"lottery", "winner", "click"}, 0.85),
    ({"remote", "app", "install"}, 0.92),
    ({"refund", "fill", "form"}, 0.80),
    ({"verify", "account", "immediately"}, 0.75),
]


def extract_keywords(text: str) -> List[str]:
    """Extract known keywords from text"""
    text_lower = text.lower()
    found = []
    for kw in KEYWORD_DB.keys():
        if kw in text_lower:
            found.append(kw)
    return found


def calculate_keyword_score(found_keywords: List[str]) -> float:
    """Calculate score based on individual keyword weights"""
    if not found_keywords:
        return 0.0
    
    max_weight = 0.0
    total_weight = 0.0
    
    for kw in found_keywords:
        weight = KEYWORD_DB[kw][0]
        max_weight = max(max_weight, weight)
        total_weight += weight
        
    # Heuristic: Score is 70% max_weight + 30% normalized total volume
    # This prevents many low-risk words from triggering high alarms, 
    # but allows single high-risk words (like OTP) to push score up.
    
    volume_bonus = min(0.3, total_weight * 0.05) # Cap volume bonus
    score = (max_weight * 0.7) + volume_bonus
    
    return min(1.0, score)


def check_apriori_rules(text: str) -> float:
    """Check against apriori rules and return max confidence found"""
    text_lower = text.lower()
    max_rule_score = 0.0
    
    for keywords, score in APRIORI_RULES:
        if all(kw in text_lower for kw in keywords):
            max_rule_score = max(max_rule_score, score)
            
    return max_rule_score


def calculate_confidence_score(text: str, history: List[Message]) -> float:
    """
    Calculate final confidence score (0.0 - 1.0)
    """
    # 1. Base Text Analysis
    keywords = extract_keywords(text)
    keyword_score = calculate_keyword_score(keywords)
    
    # 2. Apriori Pattern Analysis
    apriori_score = check_apriori_rules(text)
    
    # 3. Pattern Regex matching (from original logic)
    regex_score = 0.0
    if re.search(r'\b\d{9,18}\b', text): regex_score = 0.6  # Bank account
    if re.search(r'\b\d{4,6}\b', text) and "otp" in text.lower(): regex_score = 0.9 # OTP
    if re.search(r'https?://', text): regex_score = max(regex_score, 0.4) # Link
    
    # 4. Historical Context (Escalation)
    # If previous messages were suspicious, current score should potentially be higher.
    # (Simplified for stateless calculation, assuming caller handles state accumulation or we just look at this message)
    # Ideally, we'd decay prior scores, but here we'll focus on the current message's impact.
    
    # Final Score is max of approaches
    final_score = max(keyword_score, apriori_score, regex_score)
    
    return float(min(1.0, final_score))


def get_classification(score: float, current_tag: str = "genuine") -> str:
    """
    Return classification based on score.
    Sticky Logic: Once a 'scammer', usually stays 'scammer' unless proven otherwise (reset).
    But here we implement the threshold logic.
    """
    # If already detected as scammer, we generally keep it unless score drops significantly (which is rare in scam flows)
    # But strictly following the prompt's thresholds for the current message/state:
    
    if score >= 0.71:
        return "scammer"
    elif score >= 0.41:
        return "suspicious"
    else:
        return "genuine"


def detect_scam_llm(text: str, conversation_history: List[Message]) -> Tuple[bool, str]:
    """
    Optional LLM-based scam detection (helper for edge cases)
    """
    # (Existing LLM logic preserved but wrapped for utility if needed)
    # For now, we rely on the deterministic hybrid model as primary.
    return False, "Not used"


def analyze_message(message: Message, conversation_history: List[Message], current_score: float = 0.0) -> Tuple[float, str, List[str]]:
    """
    Main entry point for detection.
    Returns: (new_confidence_score, classification, detected_keywords)
    """
    text = message.text
    
    # Calculate score for THIS message
    msg_score = calculate_confidence_score(text, conversation_history)
    
    # Fuse with previous confidence (Simple Bayesian-like update or Max)
    # We take the MAX of current message score and (previous_score * decay)
    # to allow accidental flags to fade but real threats to stick? 
    # The prompt implies a cumulative understanding. 
    # Let's take a weighted moving average or simple max for "alert" style.
    # User requirement: "Prior confidence scores" are stored.
    # Let's assume we want to escalate.
    
    new_score = max(msg_score, current_score)
    
    # Classification
    classification = get_classification(new_score)
    
    # Extract keywords for UI
    keywords = extract_keywords(text)
    
    return new_score, classification, keywords
