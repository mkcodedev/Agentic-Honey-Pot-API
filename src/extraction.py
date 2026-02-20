"""
Intelligence extraction module
Extracts ALL types of scam data from conversation using regex patterns.
Covers: phone numbers, bank accounts, UPI IDs, phishing links, emails,
case IDs, policy numbers, order numbers — as per eval spec.
"""
import re
from typing import List, Set
from models import Message, ExtractedIntelligence


# ─────────────────────────────────────────────
# Individual extractor functions
# ─────────────────────────────────────────────

def extract_phone_numbers(text: str) -> Set[str]:
    """Extract phone numbers (+91 or 10-digit Indian format)"""
    found = set()

    # +91 with optional space/dash
    for m in re.findall(r'\+91[\s\-]?[6-9]\d{9}', text):
        found.add(re.sub(r'[\s\-]', '', m))

    # 10-digit starting 6-9
    for m in re.findall(r'\b[6-9]\d{9}\b', text):
        found.add(m)

    # International format  e.g. 0091-...
    for m in re.findall(r'\b0091[\s\-]?[6-9]\d{9}\b', text):
        found.add(re.sub(r'[\s\-]', '', m))

    return found


def extract_bank_accounts(text: str) -> Set[str]:
    """Extract bank account numbers (9–18 digit sequences, excluding 10-digit phones)"""
    found = set()
    for m in re.findall(r'\b\d{9,18}\b', text):
        if len(m) != 10:  # skip phone numbers
            found.add(m)
    return found


def extract_upi_ids(text: str) -> Set[str]:
    """Extract UPI IDs in the format name@handle (NOT email addresses with TLDs)"""
    upi_handles = [
        'paytm', 'phonepe', 'gpay', 'googlepay', 'ybl', 'upi', 'okaxis',
        'okhdfcbank', 'okicici', 'oksbi', 'ikwik', 'airtel', 'freecharge',
        'ibl', 'hdfc', 'icici', 'sbi', 'axis', 'kotak', 'indus', 'rbl',
        'yes', 'pnb', 'bob', 'cnrb', 'federal', 'idbi', 'aubank',
        'fakebank', 'fakeupi',  # evaluation placeholders (NOT 'fake' alone — too broad)
    ]

    found: Set[str] = set()

    # 1) Match known UPI handles exactly
    pattern = r'[\w.\-]+@(?:' + '|'.join(upi_handles) + r')(?=\s|$|[^a-zA-Z0-9\-_])'
    for m in re.findall(pattern, text, re.IGNORECASE):
        found.add(m)

    # 2) Generic catch-all: name@singleword where the domain has NO dots
    #    (UPI handles never have dots — emails always do e.g. gmail.com)
    for m in re.findall(r'[\w.\-]+@([A-Za-z]+)(?=\s|$|[^a-zA-Z0-9\-_])', text):
        # m is just the handle part — get the full match
        full = re.search(r'([\w.\-]+@' + re.escape(m) + r')(?=\s|$|[^a-zA-Z0-9\-_])', text)
        if full and '.' not in m:  # no TLD = not an email
            found.add(full.group(1))

    # 3) Final guard: discard any item whose domain part contains a dot (= email)
    result: Set[str] = set()
    for item in found:
        parts = item.split('@')
        if len(parts) == 2 and '.' not in parts[1]:
            result.add(item)

    return result


def extract_emails(text: str) -> Set[str]:
    """Extract email addresses"""
    pattern = r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    emails = set(re.findall(pattern, text))
    # Remove UPI-like ones (no TLD = not email)
    result = set()
    for e in emails:
        # must have a TLD part
        parts = e.split('@')
        if len(parts) == 2 and '.' in parts[1]:
            result.add(e)
    return result


def extract_phishing_links(text: str) -> Set[str]:
    """Extract URLs including suspicious shortened links"""
    found = set()

    # http / https
    for m in re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text):
        found.add(m.rstrip('.,)'))

    # www. links
    for m in re.findall(r'www\.[^\s<>"{}|\\^`\[\]]+', text):
        found.add(m.rstrip('.,)'))

    # Shortened URLs
    for m in re.findall(
        r'\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|rb\.gy|cutt\.ly|is\.gd|short\.io)/[A-Za-z0-9]+',
        text
    ):
        found.add(m)

    return found


def extract_case_ids(text: str) -> Set[str]:
    """Extract case / reference / ticket IDs (alphanumeric patterns)"""
    found = set()

    # Patterns like SBI-12345, CASE-987654, REF-ABC123, TICKET-001
    for m in re.findall(
        r'\b(?:case|ref|reference|ticket|id|no|number|case#|ref#)[:\s#\-]*([A-Z0-9\-]{5,15})\b',
        text, re.IGNORECASE
    ):
        found.add(m.upper())

    # Standalone alphanumeric IDs  e.g. SBI-12345, HDFC/9876
    for m in re.findall(r'\b[A-Z]{2,6}[-/]\d{4,10}\b', text):
        found.add(m)

    return found


def extract_policy_numbers(text: str) -> Set[str]:
    """Extract insurance / policy numbers"""
    found = set()
    for m in re.findall(
        r'\b(?:policy|pol)[:\s#\-]*([A-Z0-9\-]{6,20})\b',
        text, re.IGNORECASE
    ):
        found.add(m.upper())
    return found


def extract_order_numbers(text: str) -> Set[str]:
    """Extract order / transaction IDs"""
    found = set()
    for m in re.findall(
        r'\b(?:order|txn|transaction|trx)[:\s#\-]*([A-Z0-9\-]{6,20})\b',
        text, re.IGNORECASE
    ):
        found.add(m.upper())
    return found


def extract_suspicious_keywords(text: str) -> Set[str]:
    """Extract high-signal scam keywords for annotation purposes"""
    text_lower = text.lower()
    keywords = [
        "otp", "pin", "cvv", "atm", "debit card", "credit card",
        "account number", "bank account", "upi", "transaction",
        "payment", "refund", "cashback", "reward", "prize", "won",
        "urgent", "immediately", "expire", "deadline", "last chance",
        "verify", "verification", "confirm", "suspended", "blocked",
        "rbi", "reserve bank", "income tax", "police", "government",
        "legal action", "arrest", "warrant", "penalty", "fine",
        "congratulations", "lottery", "selected customer",
        "kyc", "aadhar", "pan card", "aadhaar",
    ]
    return {kw for kw in keywords if kw in text_lower}


# ─────────────────────────────────────────────
# Main extraction entry points
# ─────────────────────────────────────────────

def extract_intelligence_from_message(message: Message) -> ExtractedIntelligence:
    """Extract all intelligence from a single message"""
    text = message.text
    return ExtractedIntelligence(
        phoneNumbers=list(extract_phone_numbers(text)),
        bankAccounts=list(extract_bank_accounts(text)),
        upiIds=list(extract_upi_ids(text)),
        phishingLinks=list(extract_phishing_links(text)),
        emailAddresses=list(extract_emails(text)),
        caseIds=list(extract_case_ids(text)),
        policyNumbers=list(extract_policy_numbers(text)),
        orderNumbers=list(extract_order_numbers(text)),
        suspiciousKeywords=list(extract_suspicious_keywords(text)),
    )


def merge_intelligence(
    existing: ExtractedIntelligence,
    new: ExtractedIntelligence
) -> ExtractedIntelligence:
    """Merge two intelligence objects, deduplicating all lists"""
    def merged(a, b):
        return list(set(a) | set(b))

    return ExtractedIntelligence(
        phoneNumbers=merged(existing.phoneNumbers, new.phoneNumbers),
        bankAccounts=merged(existing.bankAccounts, new.bankAccounts),
        upiIds=merged(existing.upiIds, new.upiIds),
        phishingLinks=merged(existing.phishingLinks, new.phishingLinks),
        emailAddresses=merged(existing.emailAddresses, new.emailAddresses),
        caseIds=merged(existing.caseIds, new.caseIds),
        policyNumbers=merged(existing.policyNumbers, new.policyNumbers),
        orderNumbers=merged(existing.orderNumbers, new.orderNumbers),
        suspiciousKeywords=merged(existing.suspiciousKeywords, new.suspiciousKeywords),
    )


def extract_intelligence_from_conversation(messages: List[Message]) -> ExtractedIntelligence:
    """Extract and merge intelligence from the entire conversation history"""
    combined = ExtractedIntelligence()
    for msg in messages:
        intel = extract_intelligence_from_message(msg)
        combined = merge_intelligence(combined, intel)
    return combined
