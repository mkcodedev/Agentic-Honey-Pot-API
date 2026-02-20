"""
AI Agent module — generates human-like honeypot responses to keep scammers engaged.
Uses Google Gemini (LLM) when configured, falls back to rich rule-based templates.
Designed to maximise turn count, questions asked, red flags identified,
and information elicitation — all scored in the evaluation rubric.
"""
import os
import random
from typing import List, Optional
from models import Message


# ─────────────────────────────────────────────
# Rule-based response templates
# ─────────────────────────────────────────────

CONFUSED_RESPONSES = [
    "Oh dear, I'm quite confused. Could you explain that again more clearly?",
    "Wait wait wait, I didn't understand that. Can you say it differently?",
    "Sorry beta, I'm not good with all this. What exactly do you need?",
    "Hmm, I'm not following. Can you slow down a bit and explain step by step?",
    "I'm getting worried now. What exactly has happened to my account?",
    "Arre yaar, I'm an old man, these things confuse me terribly. Explain again?",
]

COOPERATIVE_RESPONSES = [
    "Okay, okay, I want to fix this. Please tell me exactly what to do.",
    "I see, this sounds serious. What information do you need from me?",
    "Alright, I trust you. What are the next steps I should follow?",
    "Yes yes, I want to cooperate. How can I help resolve this?",
    "I'm trying my best. What should I do now?",
]

STALLING_RESPONSES = [
    "Let me see... where did I keep that passbook? Can you hold on a moment?",
    "Just give me a minute, I need to find my phone. It's somewhere here...",
    "I'm trying to remember. My memory isn't what it used to be. What was that again?",
    "Hold on, my spectacles are missing. Can you repeat that slowly?",
    "I'm checking right now. The phone is loading so slow these days...",
]

ELICITATION_QUESTIONS = [
    "Can you give me your employee ID so I can verify you are genuine?",
    "Which bank branch are you calling from? What is the address?",
    "Can you share your official phone number so I can call you back?",
    "What is the exact name of your department so I can cross-check?",
    "Can you give me your supervisor's name and number? I want to verify.",
    "Is there an official website I can check your details on?",
    "What is the case reference number for this matter?",
    "Can you send an official email to confirm before I share anything?",
]

PHONE_PROBING = [
    "You want me to call you back? What is your official number?",
    "Before I do anything, please give me your direct phone number.",
    "What callback number should I use if I get disconnected?",
]

LINK_SKEPTIC = [
    "That link is not opening on my phone. Can you please send it again?",
    "I'm not sure I should click that. Is there an alternative way?",
    "My internet is slow. What happens when I click that link?",
    "I clicked it but nothing happened. What exactly should appear on the screen?",
]

RED_FLAG_CALLOUTS = [
    "Why is this so urgent? Legitimate banks usually send a proper notice.",
    "Real officers don't usually ask for OTP over a call. Are you sure this is proper?",
    "I've heard about scams like this. How can I be sure you are genuine?",
    "My son told me never to share OTP with anyone. Why do you need it?",
    "Why are you asking for money? Real banks never ask customers to pay fees.",
    "This seems unusual. Can I come to the branch directly instead?",
]

# Per-scam-type specific questions
SCAM_TYPE_PROBES = {
    "bank_fraud": [
        "Which specific branch is this call from? Can you give the branch code?",
        "Is my account still showing in my mobile banking? Let me check...",
        "Should I visit the branch personally to resolve this?",
        "Can I speak with the branch manager to confirm this?",
    ],
    "upi_fraud": [
        "I don't know my UPI ID. How do I find it?",
        "I use Google Pay, is that the same as UPI?",
        "What happens if I send a test amount of 1 rupee first?",
        "Why do you need my UPI PIN? I thought you said you would send money TO me?",
    ],
    "phishing": [
        "That website address looks strange. It doesn't look like the real bank site.",
        "I'm scared to click unknown links. Can you dictate the contents to me?",
        "My grandson says never click links from unknown callers. Why is this safe?",
        "Hmm, what is my login ID for that site exactly?",
    ],
    "lottery_fraud": [
        "I don't remember entering any lottery. Which lottery was this exactly?",
        "Why do I need to pay any fee if I have won? That sounds wrong.",
        "Can you send the official winning certificate by post first?",
        "What is the lottery company's registered address?",
    ],
}


def get_strategy_for_turn(turn: int) -> str:
    """Decide engagement strategy based on conversation turn number"""
    if turn <= 1:
        return "confused"
    elif turn <= 3:
        return "cooperative_questions"
    elif turn <= 5:
        return "stalling_with_elicitation"
    else:
        return "deep_probing"


def build_rule_based_response(
    message: Message,
    turn: int,
    scam_type: Optional[str] = None,
    asked_questions: int = 0
) -> str:
    """
    Build a rich rule-based response designed to:
    - Keep scammer engaged
    - Ask ≥5 investigative questions
    - Reference red flags
    - Attempt information elicitation
    """
    text_lower = message.text.lower()
    strategy = get_strategy_for_turn(turn)

    # Build response based on strategy
    parts = []

    if strategy == "confused":
        parts.append(random.choice(CONFUSED_RESPONSES))
        parts.append(random.choice(ELICITATION_QUESTIONS))

    elif strategy == "cooperative_questions":
        parts.append(random.choice(COOPERATIVE_RESPONSES))
        # Ask a relevant question based on content
        if any(w in text_lower for w in ["link", "click", "url", "website", "http"]):
            parts.append(random.choice(LINK_SKEPTIC))
        elif any(w in text_lower for w in ["phone", "number", "call", "contact"]):
            parts.append(random.choice(PHONE_PROBING))
        elif scam_type and scam_type in SCAM_TYPE_PROBES:
            parts.append(random.choice(SCAM_TYPE_PROBES[scam_type]))
        else:
            parts.append(random.choice(ELICITATION_QUESTIONS))

    elif strategy == "stalling_with_elicitation":
        parts.append(random.choice(STALLING_RESPONSES))
        # Reference a red flag
        if any(w in text_lower for w in ["urgent", "quickly", "fast", "immediately", "asap"]):
            parts.append(random.choice(RED_FLAG_CALLOUTS))
        else:
            parts.append(random.choice(ELICITATION_QUESTIONS))

    else:  # deep_probing
        # Mix of red flag callout + deep probe
        if any(w in text_lower for w in ["otp", "pin", "cvv", "password"]):
            parts.append(random.choice(RED_FLAG_CALLOUTS))
            parts.append("Before I do anything, please confirm: what is your full name, employee ID, and official phone number?")
        elif any(w in text_lower for w in ["link", "click", "website"]):
            parts.append(random.choice(LINK_SKEPTIC))
            parts.append(random.choice(ELICITATION_QUESTIONS))
        elif any(w in text_lower for w in ["send money", "transfer", "deposit", "fee"]):
            parts.append("Wait, you want me to send money? Real officials never ask for fees upfront!")
            parts.append(random.choice(PHONE_PROBING))
        else:
            parts.append(random.choice(COOPERATIVE_RESPONSES))
            if scam_type and scam_type in SCAM_TYPE_PROBES:
                parts.append(random.choice(SCAM_TYPE_PROBES[scam_type]))
            else:
                parts.append(random.choice(ELICITATION_QUESTIONS))

    return " ".join(parts)


# ─────────────────────────────────────────────
# LLM-powered response (Google Gemini)
# ─────────────────────────────────────────────

def build_llm_response(
    message: Message,
    conversation_history: List[Message],
    scam_type: Optional[str] = None,
    red_flags: Optional[List[str]] = None,
    turn: int = 0
) -> str:
    """Generate Gemini LLM response for natural, contextual engagement"""
    llm_provider = os.getenv("LLM_PROVIDER", "").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")

    if llm_provider != "gemini" or not llm_api_key:
        return build_rule_based_response(message, turn, scam_type)

    try:
        from google import genai
        client = genai.Client(api_key=llm_api_key)

        # Decide strategy
        if turn <= 2:
            strategy = "Be very confused and ask for basic clarification. Don't share any info. Ask who they are and what happened."
        elif turn <= 4:
            strategy = "Be cooperative but ask investigative questions. Request employee ID, official phone number, branch address."
        elif turn <= 6:
            strategy = "Stall for time. Say you're looking for something. Ask for their full name, supervisor name, and official website."
        else:
            strategy = "Ask aggressive investigative questions. Reference red flags like urgency. Ask for case reference number and their official email. Express doubts about legitimacy."

        # Build context
        context = "\n".join(
            f"{'SCAMMER' if m.sender == 'scammer' else 'ME'}: {m.text}"
            for m in conversation_history[-8:]
        )

        flags_note = ""
        if red_flags:
            flags_note = f"\nRed flags in their message: {', '.join(red_flags)}"

        scam_note = f"\nThis appears to be a {scam_type} scam." if scam_type else ""

        prompt = f"""You are roleplaying as Mr. Sharma, a 68-year-old retired school teacher being targeted by a scammer.

YOUR JOB: Act as a honeypot — keep the scammer engaged as long as possible, extract their contact details, 
phone numbers, UPI IDs, bank accounts, and any links they share. DO NOT reveal you know it's a scam.

PERSONA: Slightly confused, not tech-savvy, cooperative but asks many questions, speaks simple English sometimes mixing in Hindi words.
{scam_note}
{flags_note}

CONVERSATION SO FAR:
{context}

SCAMMER'S LATEST MESSAGE: {message.text}

STRATEGY FOR THIS TURN: {strategy}

RULES:
1. Keep response SHORT (2-3 sentences max)
2. Always ask at least ONE question to extract their info
3. Reference something suspicious if there is a red flag
4. Act confused or slow — stall for time
5. NEVER share real personal info (make up harmless details if needed)
6. Sound natural and human, not robotic

Respond as Mr. Sharma ONLY — no explanations, no meta-commentary:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        reply = response.text.strip()

        # Ensure it's not empty
        if not reply:
            return build_rule_based_response(message, turn, scam_type)

        return reply

    except Exception as e:
        print(f"LLM response error: {e}")
        return build_rule_based_response(message, turn, scam_type)


# ─────────────────────────────────────────────
# Main public API
# ─────────────────────────────────────────────

def generate_agent_response(
    message: Message,
    conversation_history: List[Message],
    scam_type: Optional[str] = None,
    red_flags: Optional[List[str]] = None
) -> str:
    """
    Generate a honeypot response.
    Uses LLM if configured, otherwise falls back to rich rule-based templates.
    """
    turn = len(conversation_history)

    if os.getenv("LLM_PROVIDER") == "gemini" and os.getenv("LLM_API_KEY"):
        return build_llm_response(message, conversation_history, scam_type, red_flags, turn)
    else:
        return build_rule_based_response(message, turn, scam_type)
