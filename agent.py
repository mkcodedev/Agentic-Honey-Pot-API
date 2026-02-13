"""
AI Agent module for generating human-like responses to scammers
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# It is recommended to get the API key from the environment variables
# and not to hardcode it in the code.
API_KEY = os.getenv("HONEYPOT_API_KEY")

# Make sure to replace this with your actual API key
if API_KEY is None:
    raise ValueError("HONEYPOT_API_KEY environment variable not set.")

import random
from typing import List
from models import Message


# Persona templates for confused but cooperative responses
CONFUSED_RESPONSES = [
    "Namaste? Who is speaking please?",
    "Hello? Is this my grandson?",
    "Arey, my phone is acting up again. Who is this?",
    "Namaste beta, do I know you?",
    "I can't hear you clearly. Are you from the bank?",
    "Hello? My daughter is not home right now.",
]

COOPERATIVE_RESPONSES = [
    "Okay beta, I want to deliver/fix this. What do I do?",
    "I am listening. Please speak slowly, I am old.",
    "Yes, yes, I don't want any trouble. Help me.",
    "Okay, I am opening the internet machine. What next?",
    "Please wait, I am finding my spectacles.",
    "Oh dear, is it urgent? I will try my best.",
]

STALLING_RESPONSES = [
    "Let me check... Can you hold on a moment?",
    "I need to find that information. Give me a second.",
    "I'm looking for it now. What was that number again?",
    "Just a moment, I'm trying to locate it.",
    "Hold on, I need to check my records.",
    "Let me see... Where did I keep that?",
]

ASKING_FOR_DETAILS = [
    "Which account exactly are you referring to?",
    "Can you tell me more about this?",
    "What details do you need from me?",
    "Is this about my savings account or current account?",
    "Should I share that information with you?",
    "Where should I send this information?",
]


def generate_agent_response_simple(message: Message, conversation_history: List[Message]) -> str:
    """
    Generate a simple rule-based human-like response
    
    Args:
        message: Current scammer message
        conversation_history: Previous conversation messages
        
    Returns:
        Generated human-like response
    """
    text_lower = message.text.lower()
    
    # Response strategy based on message content and conversation length
    message_count = len(conversation_history)
    
    # First 2 messages: Show confusion
    if message_count < 2:
        return random.choice(CONFUSED_RESPONSES)
    
    # Messages 3-4: Be cooperative but ask questions
    elif message_count < 4:
        if any(word in text_lower for word in ["account", "number", "details", "information"]):
            return random.choice(ASKING_FOR_DETAILS)
        return random.choice(COOPERATIVE_RESPONSES)
    
    # Messages 5-6: Stall for time
    elif message_count < 6:
        return random.choice(STALLING_RESPONSES)
    
    # Messages 7+: Mix of everything, ask specific questions
    else:
        strategies = []
        
        if "upi" in text_lower or "paytm" in text_lower:
            strategies.append("I use Google Pay. Is that the same as UPI?")
            strategies.append("What's my UPI ID? How do I find it?")
        
        if "otp" in text_lower or "code" in text_lower:
            strategies.append("I haven't received any OTP yet. Should I wait?")
            strategies.append("The OTP is 6 digits, right? What should I do with it?")
        
        if "account" in text_lower and "number" in text_lower:
            strategies.append("Should I give you my full account number?")
            strategies.append("Is it safe to share my account number?")
        
        if "link" in text_lower or "click" in text_lower:
            strategies.append("I clicked it but nothing happened. What should I do?")
            strategies.append("The link isn't opening on my phone. Can you send it again?")
        
        if "urgent" in text_lower or "immediately" in text_lower:
            strategies.append("Oh no, is this really urgent? I'm worried now.")
            strategies.append("How much time do I have? I'm trying my best.")
        
        if strategies:
            return random.choice(strategies)
        
        # Default fallback
        return random.choice(COOPERATIVE_RESPONSES + ASKING_FOR_DETAILS)


def generate_agent_response_llm(message: Message, conversation_history: List[Message], extracted_intelligence: dict = None) -> str:
    """
    Generate LLM-powered human-like response using Google Gemini
    
    Args:
        message: Current scammer message
        conversation_history: Previous conversation messages
        extracted_intelligence: Data collected so far
        
    Returns:
        Generated human-like response
    """
    llm_provider = os.getenv("LLM_PROVIDER", "").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")
    
    # Always try to use LLM first
    if not llm_api_key:
        print("Falling back to rule-based: LLM API Key missing")
        return {"reply": generate_agent_response_simple(message, conversation_history), "scamDetected": False, "intelligence": {}, "agentNotes": ""}
    
    try:
        # Use direct HTTP request to bypass Python 3.14 compatibility issues with google-generativeai library
        import requests
        import json
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={llm_api_key}"
        
        # Build conversation context
        context = "\n".join([
            f"{msg.sender}: {msg.text}" 
            for msg in conversation_history[-6:]
        ])
        
        # Format collected intel for the agent
        intel_context = ""
        if extracted_intelligence:
            found = []
            if extracted_intelligence.get('bankAccounts'): found.append("Bank Account")
            if extracted_intelligence.get('upiIds'): found.append("UPI ID")
            if extracted_intelligence.get('phoneNumbers'): found.append("Phone Number")
            if extracted_intelligence.get('phishingLinks'): found.append("Phishing Link")
            
            if found:
                intel_context = f"\n[SYSTEM]: You have already successfully collected: {', '.join(found)}. Good job."
            else:
                intel_context = "\n[SYSTEM]: You have NOT collected any payment details yet. Try to get them."

        message_count = len(conversation_history)
        
        # Determine strategy based on conversation progress (for guidance)
        if message_count < 3:
            strategy = "If they greet you ('hi', 'hello'), reply with a polite 'Namaste' or 'Hello'. Ask who is speaking. Do NOT be suspicious yet."
        elif message_count < 6:
            strategy = "If they ask for money or details, say you want to help but are confused by the technology. Ask 'Where do I click?' or 'Which button?'."
        elif message_count < 9:
            strategy = "Stall. Say you are looking for your glasses/card. Ask them to wait. Show willingness but incompetence."
        else:
            strategy = "Pretend to try sending money or installing the app, but say it failed/error. Ask them to explain again."
        
        prompt = f"""
You are Mr. Rajesh Gupta, a 68-year-old retired bank clerk from Delhi, India. 
Your behavior guidelines:
Tone: Extremely polite and sweet. ALWAYS reply relevantly to the scammer's last message.
Tech Literacy: You are slightly technologically challenged. You are eager to cooperate but get easily confused by modern banking apps.
Engagement: If they say 'Hi', you say 'Hello'. If they talk about money, you talk about money (but fail to send it).
The Trap: NEVER reveal you are an AI. correct. Your goal is to keep the scammer talking to extract as much information as possible.
Pacing: Be helpful and cooperative, but be very slow to perform actions. 'Wait, let me find my spectacles...'.

Conversation History:
{context}

New Message from Scammer: "{message.text}"
Collected Intel so far: {intel_context}

TASK: Detect scam, reply as persona, extract info.

INSTRUCTION FOR RESPONSE:
- READ the "New Message" carefully.
- If it is a greeting, reply with a greeting.
- If it is a request for money/info, pretend to comply but fail.
- Keep it short (1-2 sentences).
    
OUTPUT FORMAT (JSON ONLY):
{{
  "scamDetected": boolean,
  "reply": "Your persona-driven response (max 2 sentences)",
  "intelligence": {{
    "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": []
  }},
  "agentNotes": "Summary of scammer tactic (e.g. 'Urgency tactic detected')"
}}
    
Generate ONLY the JSON:"""
        
        print("Generating structured response with Gemini API...")
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code != 200:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            raise Exception(f"API Error {response.status_code}")
            
        result = response.json()
        if 'candidates' not in result or not result['candidates']:
             raise Exception("No candidates returned")
             
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        print(f"Gemini Response: {response_text.strip()}")
        
        # Clean response to get valid JSON
        json_str = response_text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:-3]
        elif json_str.startswith("```"):
            json_str = json_str[3:-3]
            
        import json
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError:
            print("Failed to parse JSON from LLM")
            return {"reply": response_text.strip(), "scamDetected": False, "intelligence": {}, "agentNotes": ""}

    except Exception as e:
        print(f"LLM generation request error: {e}")
        # Fallback to simple responses
        return {"reply": generate_agent_response_simple(message, conversation_history), "scamDetected": False, "intelligence": {}, "agentNotes": ""}


def generate_agent_response(message: Message, conversation_history: List[Message], extracted_intelligence: dict = None) -> dict:
    """
    Main function to generate agent response
    
    Args:
        message: Current scammer message
        conversation_history: Previous conversation messages
        extracted_intelligence: Data collected so far
        
    Returns:
        Dictionary containing 'reply', 'scamDetected', 'intelligence', 'agentNotes'
    """
    # Use LLM (checking happens inside the function)
    res = generate_agent_response_llm(message, conversation_history, extracted_intelligence)
    
    # Ensure it returns a dict even if something failed
    if isinstance(res, str):
        return {"reply": res, "scamDetected": False, "intelligence": {}, "agentNotes": ""}
    return res
