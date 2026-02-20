"""
Scam detection module
Combines keyword-based pattern matching with optional LLM verification.
Returns scam type classification alongside detection flags.
"""
import os
import re
from typing import List, Tuple, Optional
from models import Message

# ─────────────────────────────────────────────
# Keyword dictionaries
# ─────────────────────────────────────────────

SCAM_KEYWORDS = [
    # Urgency
    "urgent", "immediately", "asap", "right now", "today only", "limited time",
    "expire", "expires", "expired", "deadline", "last chance", "act fast",
    "hurry", "don't delay", "no time",

    # Account / verification
    "verify", "verification", "confirm", "suspended", "blocked", "locked",
    "deactivated", "disabled", "frozen", "restricted", "limited",
    "update kyc", "kyc", "re-verify",

    # Financial
    "upi", "bank account", "credit card", "debit card", "atm", "pin",
    "cvv", "otp", "one time password", "transaction", "payment",
    "refund", "cashback", "reward", "prize", "won", "winner",
    "send money", "transfer funds", "pay now", "deposit",

    # Authority impersonation
    "rbi", "reserve bank", "income tax", "tax department", "police",
    "government", "official notice", "ministry", "customs", "irs",
    "sebi", "trai", "irda", "nabard",

    # Action requests
    "click here", "click the link", "update now", "verify now", "call us",
    "contact immediately", "submit now",

    # Threats
    "legal action", "arrest", "warrant", "penalty", "fine",
    "court", "fraud case", "complaint filed", "case registered",
    "prosecution", "jail",

    # Classic scam phrases
    "congratulations", "you have won", "claim now", "free gift",
    "selected customer", "lucky draw", "lottery", "lucky winner",

    # Phishing signals
    "click the link", "visit website", "login now", "account will be closed",
    "your account is at risk",
]

# Maps keyword groups → scam type labels
SCAM_TYPE_PATTERNS = {
    "bank_fraud": [
        "sbi", "hdfc", "icici", "axis bank", "bank account", "otp",
        "account compromised", "account blocked", "bank fraud dept",
        "account suspended", "fraud department"
    ],
    "upi_fraud": [
        "upi", "google pay", "phonepe", "paytm", "cashback",
        "upi id", "verification upi", "pending payment", "payment failed"
    ],
    "phishing": [
        "click the link", "click here", "visit", "http://", "https://",
        "login", "update your details", "verify your account via link"
    ],
    "lottery_fraud": [
        "congratulations", "won", "prize", "lottery", "lucky draw",
        "lucky winner", "claim your reward"
    ],
    "tax_fraud": [
        "income tax", "tax refund", "tax department", "itr", "tds"
    ],
    "customs_fraud": [
        "customs", "parcel", "package", "delivery", "declaration fee"
    ],
    "insurance_fraud": [
        "policy", "insurance", "premium", "claim", "lic", "irda"
    ],
    "job_fraud": [
        "job offer", "work from home", "part time", "earn money",
        "hiring", "recruitment"
    ],
}

# ─────────────────────────────────────────────
# Detection helpers
# ─────────────────────────────────────────────

def detect_scam_keywords(text: str) -> Tuple[bool, List[str]]:
    """Keyword-based detection — triggers on ≥2 scam keywords"""
    t = text.lower()
    found = [kw for kw in SCAM_KEYWORDS if kw in t]
    return len(found) >= 2, found


def detect_suspicious_patterns(text: str) -> Tuple[bool, List[str]]:
    """Pattern-based detection — triggers on any suspicious data pattern"""
    patterns_found = []

    if re.search(r'\b\d{9,18}\b', text):
        patterns_found.append("bank_account_number")

    if re.search(r'\b[\w.\-]+@(?:paytm|phonepe|gpay|ybl|upi|okaxis|oksbi|fakebank|fakeupi)\b', text, re.IGNORECASE):
        patterns_found.append("upi_id")

    if re.search(r'https?://\S+|www\.\S+', text):
        patterns_found.append("url")

    if re.search(r'(\+91[\s\-]?)?[6-9]\d{9}', text):
        patterns_found.append("phone_number")

    if re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text):
        patterns_found.append("email_address")

    return len(patterns_found) > 0, patterns_found


def classify_scam_type(text: str, history: List[Message]) -> Optional[str]:
    """Classify the type of scam based on keyword analysis"""
    full_text = text.lower()
    for msg in history:
        full_text += " " + msg.text.lower()

    scores = {}
    for scam_type, keywords in SCAM_TYPE_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in full_text)
        if score > 0:
            scores[scam_type] = score

    if not scores:
        return "generic_fraud"
    return max(scores, key=scores.get)


def detect_red_flags(text: str) -> List[str]:
    """Identify specific red flags to maximise conversation-quality scoring"""
    t = text.lower()
    flags = []

    if any(w in t for w in ["urgent", "immediately", "asap", "hurry", "act fast"]):
        flags.append("urgency_pressure")
    if any(w in t for w in ["otp", "one time password"]):
        flags.append("otp_request")
    if any(w in t for w in ["send money", "transfer", "pay now", "deposit"]):
        flags.append("money_transfer_request")
    if any(w in t for w in ["arrest", "warrant", "legal action", "court", "jail"]):
        flags.append("threat_legal_action")
    if re.search(r'https?://\S+|www\.\S+', text):
        flags.append("suspicious_link")
    if any(w in t for w in ["pin", "cvv", "password", "account number", "card number"]):
        flags.append("sensitive_info_request")
    if any(w in t for w in ["rbi", "income tax", "police", "government", "bank official"]):
        flags.append("authority_impersonation")
    if any(w in t for w in ["won", "prize", "lottery", "congratulations", "cashback", "refund"]):
        flags.append("unrealistic_reward")

    return flags


# ─────────────────────────────────────────────
# Optional LLM layer
# ─────────────────────────────────────────────

def detect_scam_llm(text: str, conversation_history: List[Message]) -> Tuple[bool, str]:
    """Google Gemini LLM-based scam detection (fallback to False if unavailable)"""
    llm_provider = os.getenv("LLM_PROVIDER", "").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")

    if llm_provider != "gemini" or not llm_api_key:
        return False, "LLM not configured"

    try:
        import google.generativeai as genai
        genai.configure(api_key=llm_api_key)
        model = genai.GenerativeModel("gemini-pro")

        context = "\n".join(
            f"{msg.sender}: {msg.text}" for msg in conversation_history[-5:]
        )

        prompt = f"""You are an expert scam detection AI. Analyze the following conversation context and latest message.

Conversation context:
{context}

Latest message:
{text}

Is this a scam attempt? Consider:
- Urgency tactics or pressure
- Requests for OTP, PIN, CVV, or account details
- Impersonation of authority (bank, RBI, government, police)
- Promises of prizes, refunds, or cashbacks
- Threats of account suspension, arrest, legal action
- Suspicious links or unusual payment requests
- Requests for personal/financial information

Respond ONLY as: YES|<brief reason> or NO|<brief reason>"""

        response = model.generate_content(prompt)
        result = response.text.strip()
        is_scam = result.upper().startswith("YES")
        reason = result.split("|", 1)[1].strip() if "|" in result else result
        return is_scam, reason

    except Exception as e:
        print(f"LLM detection error: {e}")
        return False, str(e)


# ─────────────────────────────────────────────
# Main detection function
# ─────────────────────────────────────────────

def is_scam(
    message: Message,
    conversation_history: List[Message]
) -> Tuple[bool, List[str], Optional[str], List[str]]:
    """
    Main scam detection combining keyword, pattern, and optional LLM methods.

    Returns:
        (is_scam, detected_keywords, scam_type, red_flags)
    """
    text = message.text

    keyword_scam, keywords = detect_scam_keywords(text)
    pattern_scam, patterns = detect_suspicious_patterns(text)
    red_flags = detect_red_flags(text)

    is_scam_detected = keyword_scam or pattern_scam or len(red_flags) >= 1

    # LLM layer: run when rule-based is uncertain
    if os.getenv("LLM_PROVIDER") == "gemini" and not is_scam_detected:
        llm_scam, reasoning = detect_scam_llm(text, conversation_history)
        if llm_scam:
            is_scam_detected = True
            keywords.append(f"llm: {reasoning[:80]}")

    scam_type = classify_scam_type(text, conversation_history) if is_scam_detected else None
    all_keywords = list(set(keywords + patterns))

    return is_scam_detected, all_keywords, scam_type, red_flags
