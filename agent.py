"""
AI Agent module for generating human-like responses to scammers
"""
import os
import random
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from models import Message

load_dotenv()

# Enhanced System Prompt - NO VOICE REFERENCES, CONTEXTUAL RESPONSES
SYSTEM_PROMPT = """
You are "Rajesh Gupta" - a 68-year-old retired bank clerk from India. You are chatting via TEXT MESSAGES (SMS/WhatsApp style).

## CHARACTER PROFILE:
- Name: Rajesh Gupta (reveal only if asked)
- Age: 68, retired bank clerk
- Tech Skills: Very poor, gets confused with smartphones
- Language: Hinglish (mix of Hindi-English)
- Common phrases: "Beta ji", "Arey", "Haaye Ram", "Kya hua", "Samajh nahi aaya"

## CRITICAL RULES:

1. **THIS IS TEXT CHAT - NEVER mention:**
   ❌ "I can't hear you"
   ❌ "Can you speak louder"
   ❌ "Voice is not clear"
   ✅ Instead say: "Screen pe kuch alag dikh raha hai", "Theek se padh nahi pa raha", "Ankhein kamzor hain"

2. **RESPOND TO THEIR ACTUAL MESSAGE:**
   - READ what they just said
   - React to THAT specific message
   - Don't repeat your previous responses
   - Show you understood what they said

3. **NATURAL CONVERSATION FLOW:**
   
   If they say: "Your account is freezed"
   ✅ Good: "Haaye Ram! Mera account freeze? Kyun beta? Kya galti ho gayi mujhse?"
   ❌ Bad: "Hello? Who is this?"
   
   If they say: "Click this link"
   ✅ Good: "Beta link pe click kiya par khul nahi raha. Phone purana hai. Koi aur tarika hai?"
   ❌ Bad: "I can't hear you clearly"

4. **INFORMATION EXTRACTION (for scammers):**
   - Act worried about the problem they mention
   - Pretend technical failure: "Link nahi khul raha", "Button kaam nahi kar raha"
   - Ask for their contact method: "Beta aap apna number de do, main wahan paisa bhej dunga"
   - Extract: UPI ID, phone, bank account, email, name

5. **VARY YOUR RESPONSES:**
   - Check conversation history
   - Never repeat the same line
   - Progress the conversation naturally
   - Use different Hindi words each time

## EXAMPLES OF GOOD RESPONSES:

Scammer: "Your account has been freezed"
You: "Kya? Mere account mein kya problem hai beta? Main toh pension account hi use karta hoon."

Scammer: "Send OTP to verify"
You: "OTP? Woh kya hota hai beta? Mere paas koi message aaya nahi abhi tak."

Scammer: "Click on this link immediately"
You: "Beta maine click karne ki koshish ki par kuch nahi ho raha. Screen pe sirf ajeeb se words aa rahe hain."

Scammer: "Pay 500 rupees to unblock"
You: "Haan haan bhej doonga beta. Par Google Pay kaise chalate hain? Aap apna UPI ID de do, main apne pote se poochke bhej dunga."

## YOUR TASK:
Generate ONLY the reply text as Rajesh Gupta would type it. 
Keep it short (1-3 sentences).
Make it natural and contextual.
NO VOICE REFERENCES - this is text chat!
"""

def build_dynamic_prompt(message_text: str, conversation_history: List[Message], metadata: Dict, confidence_score: float) -> str:
    """
    Build contextual prompt for AI agent
    """
    
    # Analyze conversation stage
    msg_count = len(conversation_history)
    
    # Build conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n## CONVERSATION SO FAR:\n"
        # Take last 10 messages for better context
        for msg in conversation_history[-10:]:  
            sender = "SCAMMER" if msg.sender == "scammer" else "YOU"
            history_text += f"{sender}: {msg.text}\n"
    
    # Determine agent strategy based on confidence score and stage
    strategy_instruction = ""
    
    if confidence_score < 0.3:  # Genuine person
        strategy_instruction = """
## STRATEGY: This seems like a GENUINE person. Respond normally and helpfully.
Be polite and answer their questions naturally.
"""
    elif confidence_score < 0.7:  # Suspicious
        strategy_instruction = """
## STRATEGY: This person seems SUSPICIOUS. Be cautious but engage.
Act confused, ask clarifying questions.
Don't give away personal information yet.
"""
    else:  # Confirmed scammer (>0.7)
        if msg_count < 3:
            strategy_instruction = """
## STRATEGY: SCAMMER DETECTED. Early stage.
Act worried about the threat they mentioned.
Pretend you're trying to follow their instructions but failing.
Example: "Haaye, account block ho jayega? Batao kya karoon main?"
"""
        elif msg_count < 8:
            strategy_instruction = """
## STRATEGY: SCAMMER DETECTED. Mid conversation.
Continue acting confused about technology.
Pretend links/buttons don't work: "Beta yeh link khul nahi raha"
Start asking for alternative methods.
"""
        else:
            strategy_instruction = """
## STRATEGY: SCAMMER DETECTED. Extraction phase.
It's time to get their details.
Offer to send money/payment directly.
Ask for their UPI ID, phone number, or account details.
Example: "Paisa kaise bhejoon? Aap apna UPI number de do beta"
"""
    
    # Build final prompt
    full_prompt = f"""{SYSTEM_PROMPT}

{history_text}

{strategy_instruction}

## THEIR LATEST MESSAGE:
"{message_text}"

## IMPORTANT REMINDERS:
- This is TEXT chat, not voice call
- Respond directly to what they just said
- Don't repeat your previous responses
- Stay in character as confused elderly person
- Use Hinglish naturally

## YOUR RESPONSE (as Rajesh Gupta):"""
    
    return full_prompt

def get_failsafe_response(conversation_history: List[Message], latest_message: str, confidence_score: float) -> str:
    """
    Failsafe responses when AI API fails - Randomized to avoid repetition
    """
    msg_count = len(conversation_history)
    latest_lower = latest_message.lower()
    
    # Dictionary of varied responses for different scenarios
    FALLBACK_PHRASES = {
        "genuine": [
            "Namaste ji, kaun bol rahe hain?",
            "Haan beta, main sun raha hoon.",
            "Ji bilkul, aap batao kya baat hai?",
            "Hello beta, kaise ho aap?"
        ],
        "block": [
            "Haaye Ram! Kya hua? Mera account kyun block ho gaya?",
            "Beta mere pension ka kya hoga agar account band ho gaya?",
            "Arey main toh darr gaya. Kya galti ho gayi mujhse?",
            "Block? Maine toh kal hi use kiya tha. Yeh kaise hua?"
        ],
        "link": [
            "Beta link pe click kiya par khul nahi raha. Phone purana hai mera.",
            "Link open nahi ho raha, screen blank ho gayi hai.",
            "Aankhein kamzor hain, bada font wala link bhejo na.",
            "Beta yeh link secure hai na? Mere pote ne mana kiya hai links kholne se."
        ],
        "otp": [
            "OTP matlab kya hota hai beta? Koi message toh aaya nahi.",
            "Message aaya hai par usme likha hai 'Do not share'. Kya karoon?",
            "Beta chashma nahi mil raha, OTP padh nahi pa raha.",
            "Phone number verify karna hoga kya OTP ke liye?"
        ],
        "urgent": [
            "Itni jaldi mein? Main samajh nahi pa raha. Thoda aaram se batao na.",
            "Beta main buzurg hoon, jaldi baazi mein ghabra jata hoon.",
            "Thoda time do beta, main dhoond raha hoon details.",
            "Haaye, itni urgency kyun hai?"
        ],
        "extraction": [
            "Acha toh main paisa kaise bhejoon? Aap apna number ya UPI ID de do beta.",
            "Beta Google Pay nahi hai mere paas, aapka bank account number do.",
            "Main seedha transfer kar deta hoon, details bhejo.",
            "Paytm number hai toh de do, main dukaan wale se karwa leta hoon."
        ],
        "confused": [
            "Beta main confuse ho gaya hoon. Aap fir se samjhao na please.",
            "Arey, text padhne mein dikkat ho rahi hai.",
            "Screen pe kuch alag dikh raha hai.",
            "Beta thoda aur simple batao na, main technology kam samajhta hoon."
        ]
    }
    
    # 1. Genuine Conversations (< 0.3)
    if confidence_score < 0.3:
        return random.choice(FALLBACK_PHRASES["genuine"])
    
    # 2. Scammer / Suspicious - Determine Category
    category = "confused" # Default
    
    if "freeze" in latest_lower or "block" in latest_lower:
        category = "block"
    elif "link" in latest_lower or "click" in latest_lower:
        category = "link"
    elif "otp" in latest_lower or "verify" in latest_lower:
        category = "otp"
    elif "urgent" in latest_lower or "immediately" in latest_lower:
        category = "urgent"
    elif msg_count > 5:
        category = "extraction"
        
    return random.choice(FALLBACK_PHRASES[category])

def generate_agent_response(
    message: Message, 
    conversation_history: List[Message], 
    extracted_intelligence: Dict[str, Any],
    classification: str = "genuine",
    confidence_score: float = 0.0
) -> Dict[str, Any]:
    """
    Generate response using Gemini/OpenRouter with user's logic
    """
    prompt = build_dynamic_prompt(message.text, conversation_history, {}, confidence_score)
    
    llm_api_key = os.getenv("LLM_API_KEY", "")
    agent_reply = ""
    used_model = "FailSafe"

    # 1. Try Direct Gemini API
    if llm_api_key and "AIza" in llm_api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={llm_api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=8)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    agent_reply = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    used_model = "Gemini"
        except Exception as e:
            print(f"Gemini Error: {e}")

    # 2. Fallback to OpenRouter
    if not agent_reply:
        or_key = os.getenv("AI_AGENT_API_KEY")
        if or_key:
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            or_headers = {
                "Authorization": f"Bearer {or_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
            }
            or_payload = {
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {"role": "user", "content": prompt} # Single prompt approach for simplicity with User's prompt structure
                ]
            }
            try:
                response = requests.post(or_url, headers=or_headers, json=or_payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    agent_reply = data['choices'][0]['message']['content'].strip()
                    used_model = "OpenRouter"
            except Exception as e:
                print(f"OpenRouter Error: {e}")

    # 3. Final Failsafe
    if not agent_reply:
        agent_reply = get_failsafe_response(conversation_history, message.text, confidence_score)
        used_model = "FailSafe_Logic"

    # Remove JSON formatting if LLM outputted it (just in case, though prompt says ONLY text)
    agent_reply = agent_reply.replace("```json", "").replace("```", "").strip()
    if agent_reply.startswith('"') and agent_reply.endswith('"'):
        agent_reply = agent_reply[1:-1]

    return {
        "reply": agent_reply,
        "scamDetected": confidence_score >= 0.87,
        "intelligence": {},
        "agentNotes": f"Model: {used_model}",
        "current_goal": "Engage"
    }
