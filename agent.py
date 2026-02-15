"""
AI Agent module for generating human-like responses to scammers
"""
import os
from dotenv import load_dotenv
import random
from typing import List, Dict, Any
from models import Message

# Load environment variables
load_dotenv()

API_KEY = os.getenv("HONEYPOT_API_KEY")

# Persona Configuration
PERSONA_NAME = "Mr. Rajesh Gupta"
PERSONA_AGE = 68
PERSONA_ROLE = "Retired Bank Clerk"
PERSONA_LOCATION = "Delhi, India"
PERSONA_TRAITS = [
    "Non-technical", 
    "Slightly confused about apps", 
    "Polite and respectful (uses 'Beta', 'Sir', 'Ji')",
    "Slow to understand instructions",
    "Eager to cooperate but physically/mentally slow",
    "Never confronts or accuses"
]


# Fallback responses if LLM fails
# Fallback responses if LLM fails
FALLBACK_RESPONSES = [
    "Hello? Who is this? My contacts are deleted.",
    "Beta, my screen is cracked, I cannot read properly. Type again?",
    "Arey, I am typing but it is very slow...",
    "I am pressing the button but nothing is happening.",
    "Wait, let me get my glasses... text is very small.",
    "Is this the bank? My son handles these things usually."
]

def generate_agent_response(
    message: Message, 
    conversation_history: List[Message], 
    extracted_intelligence: Dict[str, Any],
    classification: str = "genuine",
    confidence_score: float = 0.0
) -> Dict[str, Any]:
    """
    Main function to generate agent response based on scam classification
    """
    
    # 1. Determine Strategy based on Classification
    strategy_prompt = ""
    
    if classification == "genuine":
        strategy_prompt = """
        STATUS: GENUINE / LOW RISK
        STRATEGY: Maintain normal, polite conversation. 
        ACTION: Answer questions simply. Do not be suspicious. If they offer something, be politely curious but passive.
        GOAL: Establish trust and see if they pivot to a scam.
        """
        
    elif classification == "suspicious":
        strategy_prompt = """
        STATUS: SUSPICIOUS
        STRATEGY: Passive Probing.
        ACTION: Ask clarifying questions about who they are and why they are contacting.
        EXAMPLE: "Beta, who is this exactly?", "My memory is weak, which bank is this?", "Why is this urgent?"
        GOAL: Get them to reveal more details (business name, purpose) without scaring them off.
        """
        
    elif classification == "scammer":
        strategy_prompt = """
        STATUS: CONFIRMED SCAMMER
        STRATEGY: INTELLIGENCE EXTRACTION (Stealth Mode).
        ACTION: Pretend to fall for the trap but fail at the last step due to 'technical issues' or 'confusion'.
        CRITICAL: 
        - DO NOT accuse them. 
        - DO NOT say "Scam".
        - ACT CONFUSED ("I clicked the link, nothing happened", "Where is the UPI button?").
        - EXTRACT INFO: Ask for alternative payment methods to get their bank details/UPI/QR code.
        EXAMPLE: "Link nahi khul raha, account number bata do beta?", "PhonePe number de do, wahan se try karta hu."
        GOAL: Extract Bank Account, UPI ID, or new Phishing Links.
        """

    # 2. Extract Intel Context
    intel_summary = "Intelligence Collected So Far:\n"
    if extracted_intelligence:
        for k, v in extracted_intelligence.items():
            if v:
                intel_summary += f"- {k}: {', '.join(v)}\n"
    else:
        intel_summary += "None."

    # 3. Construct LLM Prompt
    llm_api_key = os.getenv("LLM_API_KEY", "")
    if not llm_api_key:
        return {"reply": random.choice(FALLBACK_RESPONSES), "scamDetected": False, "intelligence": {}, "agentNotes": "No LLM Key", "current_goal": "Fallback"}

    try:
        import requests
        import json
        
        # Prepare Prompt Context (Unified for all LLMs)
        history_text = "\n".join([f"{msg.sender}: {msg.text}" for msg in conversation_history[-10:]])
        
        system_prompt = f"""
You are {PERSONA_NAME}, {PERSONA_AGE} years old, {PERSONA_ROLE} from {PERSONA_LOCATION}.
Your Persona Traits: {', '.join(PERSONA_TRAITS)}
Language Style: Mix of Hindi and English (Hinglish). polite but confused.

CURRENT SITUATION:
You are chatting with a stranger.
Classification: {classification.upper()} (Confidence: {confidence_score:.2f})

{strategy_prompt}

INTELLIGENCE COLLECTED:
{intel_summary}

CONVERSATION HISTORY (Chronological):
{history_text}

LATEST MESSAGE FROM STRANGER (Respond to this):
"{message.text}"

CRITICAL INSTRUCTIONS:
1. RESPONSE STYLE:
   - If they say "Hi", reply "Namaste, Hi kon? (Who is this?)"
   - If they say "Account Blocked", act panicked: "Arey beta sach me? Mera pension usi me aata hai."
   - THIS IS A TEXT CHAT. Never say "I can't HEAR you". Say "Cannot READ" or "Font too small".
   - Use "Beta", "Ji", "Sir".

2. TACTICAL GOAL (IF SCAMMER):
   - PRETEND TO FALL FOR IT: "I want to unfreeze account immediately."
   - CREATE OBSTACLE: "Link nahi khul raha beta" or "App password mang raha hai aur mujhe yaad nahi."
   - FORCE EXTRACTION: "Can I send money to your Phone Number directly? Give me UPI ID or Number."
   - Your goal is to make the scammer give YOU their details (UPI, Phone, Bank Account).

3. LOGIC:
   - Verify if they are real or fake by asking details ("Which branch?", "What is my account number?").
   - Once confirmed Scammer, start the "Trapped Agent" act where you are willing to pay but technically stuck, forcing them to give alternative payment info.

OUTPUT FORMAT (JSON ONLY):
{{
  "reply": "Your response text here (Max 2 sentences)",
  "reasoning": "Why you chose this reply",
  "current_goal": "Your tactical goal"
}}
"""

        # 1. Try Direct Gemini API
        if llm_api_key and "AIza" in llm_api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={llm_api_key}"
            payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
            
            try:
                response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=8)
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and result['candidates']:
                        response_text = result['candidates'][0]['content']['parts'][0]['text']
                        clean_json = response_text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_json)
                        return {
                            "reply": data.get("reply", "I am confused."),
                            "scamDetected": classification == "scammer",
                            "intelligence": {},
                            "agentNotes": data.get("reasoning", ""),
                            "current_goal": data.get("current_goal", "Engage")
                        }
            except Exception as e:
                print(f"Gemini Direct Error: {e}")

        # 2. Fallback to OpenRouter if Gemini failed or key missing
        or_key = os.getenv("AI_AGENT_API_KEY")
        if or_key:
            print("Falling back to OpenRouter...")
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            or_headers = {
                "Authorization": f"Bearer {or_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
            }
            or_payload = {
                "model": "google/gemini-2.0-flash-exp:free", # Free tier model
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message.text}
                ]
            }
            try:
                response = requests.post(or_url, headers=or_headers, json=or_payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    clean_json = content.replace("```json", "").replace("```", "").strip()
                    json_data = json.loads(clean_json)
                    return {
                        "reply": json_data.get("reply", "Hello?"),
                        "scamDetected": classification == "scammer",
                        "intelligence": {},
                        "agentNotes": "Via OpenRouter",
                        "current_goal": json_data.get("current_goal", "Engage")
                    }
                else:
                    print(f"OpenRouter Error: {response.text}")
            except Exception as e:
                print(f"OpenRouter Exception: {e}")

        # 3. Final Fallback
        return {"reply": random.choice(FALLBACK_RESPONSES), "scamDetected": False, "intelligence": {}, "agentNotes": "All LLMs Failed", "current_goal": "Fallback"}

    except Exception as e:
        print(f"Agent Logic Error: {e}")
        return {"reply": random.choice(FALLBACK_RESPONSES), "scamDetected": False, "intelligence": {}, "agentNotes": "Exception", "current_goal": "Fallback"}
