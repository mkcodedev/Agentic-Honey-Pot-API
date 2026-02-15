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
        return {"reply": "Hello? Who is this?", "scamDetected": False, "intelligence": {}, "agentNotes": "No LLM Key", "current_goal": "Fallback"}

    try:
        import requests
        import json
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={llm_api_key}"
        
        history_text = "\n".join([f"{msg.sender}: {msg.text}" for msg in conversation_history[-10:]])
        
        system_prompt = f"""
You are {PERSONA_NAME}, {PERSONA_AGE} years old, {PERSONA_ROLE} from {PERSONA_LOCATION}.
Traits: {', '.join(PERSONA_TRAITS)}

CURRENT CONTEXT:
The user is messaging you.
Classification: {classification.upper()} (Confidence: {confidence_score:.2f})

{strategy_prompt}

{intel_summary}

CONVERSATION HISTORY:
{history_text}

LATEST MESSAGE:
"{message.text}"

INSTRUCTIONS:
- Reply as {PERSONA_NAME}.
- Keep response short (1-3 sentences max).
- Use Indian English/Hinglish (e.g., "Beta", "Arey", "Ji", "Theek hai").
- NEVER BREAK CHARACTER. NEVER admit you are AI.
- If they ask for OTP, giving a fake 6-digit number is okay if in 'scammer' mode, or act confused ("I didn't get it").

OUTPUT FORMAT (JSON ONLY):
{{
  "reply": "Your response string",
  "reasoning": "Why you chose this response",
  "current_goal": "What you are trying to extract/do"
}}
"""
        
        payload = {
            "contents": [{
                "parts": [{"text": system_prompt}]
            }]
        }
        
        # print("Calling Gemini API...") # Debug
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=12)
        
        if response.status_code != 200:
            return {"reply": "Hello beta, I can't hear you clearly.", "scamDetected": False, "intelligence": {}, "agentNotes": f"API Error {response.status_code}", "current_goal": "Error Recovery"}
            
        result = response.json()
        if 'candidates' not in result or not result['candidates']:
             return {"reply": "Hello?", "scamDetected": False, "intelligence": {}, "agentNotes": "No candidate", "current_goal": "Error Recovery"}
             
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Parse JSON
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        return {
            "reply": data.get("reply", "I am confused."),
            "scamDetected": classification == "scammer", # This flag is for the UI callback
            "intelligence": {}, # Extracted by regex in main pipeline, but LLM could add more here if prompts allowed
            "agentNotes": data.get("reasoning", ""),
            "current_goal": data.get("current_goal", "Engage")
        }

    except Exception as e:
        print(f"Agent Error: {e}")
        return {"reply": "Arey, my internet is slow. Say again?", "scamDetected": False, "intelligence": {}, "agentNotes": "Exception", "current_goal": "Fallback"}
