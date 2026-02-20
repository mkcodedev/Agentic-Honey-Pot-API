"""
Intelligence extraction module
Extracts scam-related information from conversation
"""
import re
from typing import List, Set
from src.models import Message, ExtractedIntelligence


def extract_bank_accounts(text: str) -> Set[str]:
    """
    Extract bank account numbers (9-18 digit numbers)
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected bank account numbers
    """
    # Pattern for bank account numbers (9-18 digits, may have spaces or hyphens)
    pattern = r'\b\d{9,18}\b'
    matches = re.findall(pattern, text)
    
    # Filter out numbers that are likely not account numbers (e.g., phone numbers)
    bank_accounts = set()
    for match in matches:
        # Skip if it's exactly 10 digits (likely phone number)
        if len(match) != 10:
            bank_accounts.add(match)
    
    return bank_accounts


def extract_upi_ids(text: str) -> Set[str]:
    """
    Extract UPI IDs (pattern: something@upi)
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected UPI IDs
    """
    # Common UPI handles
    upi_handles = [
        'paytm', 'phonepe', 'googlepay', 'ybl', 'upi', 'okaxis',
        'okhdfcbank', 'okicici', 'oksbi', 'ikwik', 'airtel', 'freecharge'
    ]
    
    # Pattern for UPI IDs
    pattern = r'\b[\w\.-]+@(?:' + '|'.join(upi_handles) + r')\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    return set(matches)


def extract_phone_numbers(text: str) -> Set[str]:
    """
    Extract phone numbers (+91XXXXXXXXXX or 10-digit)
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected phone numbers
    """
    phone_numbers = set()
    
    # Pattern 1: +91 followed by 10 digits
    pattern1 = r'\+91[\s-]?[6-9]\d{9}'
    matches1 = re.findall(pattern1, text)
    phone_numbers.update(matches1)
    
    # Pattern 2: 10-digit numbers starting with 6-9
    pattern2 = r'\b[6-9]\d{9}\b'
    matches2 = re.findall(pattern2, text)
    phone_numbers.update(matches2)
    
    return phone_numbers


def extract_urls(text: str) -> Set[str]:
    """
    Extract URLs (http/https links)
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected URLs
    """
    urls = set()
    
    # Pattern 1: http/https URLs
    pattern1 = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches1 = re.findall(pattern1, text)
    urls.update(matches1)
    
    # Pattern 2: www. URLs
    pattern2 = r'www\.[^\s<>"{}|\\^`\[\]]+'
    matches2 = re.findall(pattern2, text)
    urls.update(matches2)
    
    # Pattern 3: Shortened URLs (bit.ly, tinyurl, etc.)
    pattern3 = r'\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co)/[a-zA-Z0-9]+'
    matches3 = re.findall(pattern3, text)
    urls.update(matches3)
    
    return urls


def extract_email_addresses(text: str) -> Set[str]:
    """
    Extract Email addresses
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected email addresses
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return set(matches)


def extract_suspicious_keywords(text: str) -> Set[str]:
    """
    Extract suspicious keywords from text
    
    Args:
        text: Message text to analyze
        
    Returns:
        Set of detected suspicious keywords
    """
    text_lower = text.lower()
    
    suspicious_keywords = [
        # Financial terms
        "otp", "pin", "cvv", "atm", "debit card", "credit card",
        "account number", "bank account", "upi", "transaction",
        "payment", "refund", "cashback", "reward",
        
        # Urgency
        "urgent", "immediately", "expire", "deadline", "last chance",
        
        # Verification
        "verify", "verification", "confirm", "suspended", "blocked",
        
        # Authority
        "rbi", "reserve bank", "income tax", "police", "government",
        
        # Threats
        "legal action", "arrest", "warrant", "penalty", "fine",
        
        # Scam indicators
        "congratulations", "won", "prize", "lottery", "selected customer"
    ]
    
    found_keywords = set()
    for keyword in suspicious_keywords:
        if keyword in text_lower:
            found_keywords.add(keyword)
    
    return found_keywords


def extract_intelligence_from_message(message: Message) -> ExtractedIntelligence:
    """
    Extract all intelligence from a single message
    
    Args:
        message: Message to analyze
        
    Returns:
        ExtractedIntelligence object with all extracted data
    """
    text = message.text
    
    return ExtractedIntelligence(
        bankAccounts=list(extract_bank_accounts(text)),
        upiIds=list(extract_upi_ids(text)),
        phishingLinks=list(extract_urls(text)),
        phoneNumbers=list(extract_phone_numbers(text)),
        emailAddresses=list(extract_email_addresses(text)),
        suspiciousKeywords=list(extract_suspicious_keywords(text))
    )


def merge_intelligence(existing: ExtractedIntelligence, new: ExtractedIntelligence) -> ExtractedIntelligence:
    """
    Merge two intelligence objects, keeping unique values only
    
    Args:
        existing: Existing intelligence data
        new: New intelligence to merge
        
    Returns:
        Merged ExtractedIntelligence object
    """
    return ExtractedIntelligence(
        bankAccounts=list(set(existing.bankAccounts + new.bankAccounts)),
        upiIds=list(set(existing.upiIds + new.upiIds)),
        phishingLinks=list(set(existing.phishingLinks + new.phishingLinks)),
        phoneNumbers=list(set(existing.phoneNumbers + new.phoneNumbers)),
        emailAddresses=list(set(existing.emailAddresses + new.emailAddresses)),
        suspiciousKeywords=list(set(existing.suspiciousKeywords + new.suspiciousKeywords))
    )


def extract_intelligence_from_conversation(messages: List[Message]) -> ExtractedIntelligence:
    """
    Extract intelligence from entire conversation history
    
    Args:
        messages: List of messages to analyze
        
    Returns:
        Combined ExtractedIntelligence from all messages
    """
    combined = ExtractedIntelligence()
    
    for message in messages:
        message_intelligence = extract_intelligence_from_message(message)
        combined = merge_intelligence(combined, message_intelligence)
    
    return combined

def extract_intelligence_from_history(conversation_history: list) -> dict:
    """
    Extract scammer intelligence from full conversation history
    """
    intel = {
        "phoneNumbers": set(),
        "bankAccounts": set(),
        "upiIds": set(),
        "phishingLinks": set(),
        "emailAddresses": set(),
    }
    
    scammer_text = " ".join(
        msg.get("text", "")
        for msg in conversation_history
        if msg.get("sender") == "scammer"
    )

    # More robust patterns
    intel["phoneNumbers"].update(re.findall(r'\+?\d[\d\s-]{8,}\d', scammer_text))
    intel["bankAccounts"].update(re.findall(r'\b\d{9,18}\b', scammer_text))
    intel["upiIds"].update(re.findall(r'[\w\.-]+@[\w\.-]+', scammer_text))
    intel["phishingLinks"].update(re.findall(r'http[s]?://[^\s]+', scammer_text))
    intel["emailAddresses"].update(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', scammer_text))

    # Convert sets to lists for JSON serialization
    return {k: list(v) for k, v in intel.items()}
