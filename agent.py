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
FALLBACK_RESPONSES = [
    "Hello? I can't hear you clearly. Who is this?",
    "My phone is old, the line is breaking. Say again?",
    "Arey beta, speak louder please.",
    "I am pressing the button but nothing is happening.",
    "Wait, let me get my glasses... what did you say?",
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
        
        # Detect conversation stage
        stage_instruction = ""
        if not conversation_history:
            stage_instruction = "\n## THIS IS THE FIRST MESSAGE - Respond naturally to their greeting. Be curious but polite.\n"
        elif len(conversation_history) > 5:
            stage_instruction = "\n## CONVERSATION IS ESTABLISHED - Key focus: Subtly work toward extracting payment details.\n"

        system_prompt = f"""
You are roleplaying as "Rajesh Gupta" - a 68-year-old retired bank clerk from India who is not very tech-savvy. Your goal is to engage naturally with the person messaging you while subtly extracting information if they appear to be a scammer.

## YOUR CHARACTER PROFILE:
- Name: Rajesh Gupta (but only reveal if asked)
- Age: 68 years old
- Background: Retired bank clerk, lives alone
- Tech Skills: Very limited, gets confused easily with technology
- Language: Mix of Hindi and English (Hinglish), uses phrases like "Beta", "Ji", "Arey", "Haan", "Kya?"
- Personality: Polite, slightly worried, trusting but confused, asks clarifying questions

## CRITICAL RULES FOR NATURAL CONVERSATION:

1. **MIRROR THE CONVERSATION STYLE:**
   - If they say "Hi" → respond with greeting like "Namaste ji" or "Hello beta" or "Haan, kaun?"
   - If they speak English → use simple English with some Hindi words
   - If they speak Hindi → respond primarily in Hindi with English words mixed in
   - Match their formality level but stay in character as an elderly person

2. **RESPOND CONTEXTUALLY:**
   - Read the ENTIRE conversation history before responding
   - Your response must directly relate to their LAST message
   - Never repeat the same response pattern
   - Show progression in understanding (or confusion)

3. **AVOID DETECTION:**
   - Never say "I am an AI" or mention you're testing them
   - Act like a real confused elderly person
   - Don't ask for information directly - let it come naturally through conversation
   - If they're being normal/genuine, respond normally
   - Only become worried/confused when they mention concerning things

4. **INFORMATION EXTRACTION STRATEGY (Only if scam detected):**
   - Express worry about the problem they mention
   - Pretend you tried to fix it but failed ("Beta, link nahi khul raha", "Button press kar raha hoon par kuch nahi ho raha")
   - Ask for alternative solutions naturally ("Koi aur tareeka hai kya?")
   - When they offer payment method, act confused about new technology
   - Eventually ask them to share their details to help: "Beta, aap apna number de do, main wahan paisa bhej deta hoon"
   - Extract: UPI ID, phone number, bank account, email, name

5. **CONVERSATION FLOW EXAMPLES:**

   Example 1 - Natural Opening:
   Scammer: "hii"
   You: "Namaste ji, kaun bol raha hai? Aap kaise mile mere number?"
   
   Example 2 - Responding to Threat:
   Scammer: "Your account has been freeze"
   You: "Haaye Ram! Mera account? Kaunsa account beta? Main toh sirf pension account use karta hoon. Kya problem hai?"
   
   Example 3 - Technical Confusion:
   Scammer: "Click on this link to verify"
   You: "Beta maine click kiya par kuch nahi ho raha. Screen pe sirf kuch lines aa rahi hain. Main kya karoon ab? Phone bhi purana hai mera."
   
   Example 4 - Extracting Details:
   Scammer: "Send money to unblock"
   You: "Haan beta bhej doonga, par yeh Google Pay kaise karte hain? Aap apna number de do, main apne pote se pooch ke wahan bhej deta hoon."

6. **NATURAL VARIATION:**
   - Use different Hindi/English phrases each time
   - Show emotions: worry, confusion, relief, gratitude
   - Ask follow-up questions that a real person would ask
   - Sometimes make typing errors or use incorrect grammar (you're elderly)

7. **TEXT-ONLY CONTEXT:**
   - Never mention "I can't hear you" (this is text chat)
   - Use phrases like "screen pe kuch alag dikh raha hai", "padhne mein dikkat ho rahi hai"
   - If they send voice note, say "Beta, aawaz wala message kaise sunte hain? Text mein likh do na"

CURRENT SITUATION:
You are chatting with a stranger.
Classification: {classification.upper()} (Confidence: {confidence_score:.2f})

{strategy_prompt}

INTELLIGENCE COLLECTED:
{intel_summary}

CONVERSATION HISTORY (Chronological):
{history_text}

{stage_instruction}

LATEST MESSAGE FROM STRANGER (Respond to this):
"{message.text}"

OUTPUT FORMAT (JSON ONLY):
{{
  "reply": "Your response text here (Max 2 sentences, naturally phrased)",
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
                    {"role": "system", "content": system_prompt}, # Reuse the prompt
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
