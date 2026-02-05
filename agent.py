"""
AI Agent module for generating human-like responses to scammers
"""
import os
import random
from typing import List
from models import Message


# Persona templates for confused but cooperative responses
CONFUSED_RESPONSES = [
    "I'm not sure I understand. Can you explain again?",
    "Wait, what do you mean exactly?",
    "I'm a bit confused. Can you clarify?",
    "Sorry, I didn't quite get that. What should I do?",
    "Hmm, I'm not following. Can you help me understand?",
    "I'm not very good with these things. Can you explain step by step?",
]

COOPERATIVE_RESPONSES = [
    "Okay, I'll try to help. What do you need from me?",
    "Sure, I want to resolve this. What's next?",
    "I see. What information do you need?",
    "Alright, I'm ready to proceed. What should I do?",
    "Okay, I understand it's important. How can I help?",
    "Yes, I want to fix this. Please guide me.",
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


def generate_agent_response_llm(message: Message, conversation_history: List[Message]) -> str:
    """
    Generate LLM-powered human-like response using Google Gemini
    
    Args:
        message: Current scammer message
        conversation_history: Previous conversation messages
        
    Returns:
        Generated human-like response
    """
    llm_provider = os.getenv("LLM_PROVIDER", "").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")
    
    if llm_provider != "gemini" or not llm_api_key:
        # Fallback to simple responses if LLM not configured
        return generate_agent_response_simple(message, conversation_history)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=llm_api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Build conversation context
        context = "\n".join([
            f"{msg.sender}: {msg.text}" 
            for msg in conversation_history[-6:]
        ])
        
        message_count = len(conversation_history)
        
        # Determine strategy based on conversation progress
        if message_count < 3:
            strategy = "Be confused and ask for clarification. Don't provide any information yet."
        elif message_count < 5:
            strategy = "Be cooperative but cautious. Ask questions about what they need."
        elif message_count < 7:
            strategy = "Stall for time. Say you're looking for information or having trouble."
        else:
            strategy = "Ask specific questions about the details they're requesting. Act elderly or not tech-savvy."
        
        prompt = f"""You are roleplaying as an ordinary person who is being targeted by a scammer. 
Your goal is to keep the scammer engaged and extract more information from them WITHOUT revealing you know it's a scam.

Conversation so far:
{context}

Scammer's latest message: {message.text}

Instructions:
- {strategy}
- Keep responses SHORT (1-2 sentences max)
- Sound human and natural
- Use simple language
- Ask follow-up questions
- Never reveal you know it's a scam
- Act confused, elderly, or not tech-savvy
- Do NOT provide real personal information

Generate ONLY the response text, nothing else:"""

        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"LLM generation error: {e}")
        # Fallback to simple responses
        return generate_agent_response_simple(message, conversation_history)


def generate_agent_response(message: Message, conversation_history: List[Message]) -> str:
    """
    Main function to generate agent response
    
    Args:
        message: Current scammer message
        conversation_history: Previous conversation messages
        
    Returns:
        Generated human-like response
    """
    # Use LLM if configured, otherwise use simple rule-based
    if os.getenv("LLM_PROVIDER") == "gemini" and os.getenv("LLM_API_KEY"):
        return generate_agent_response_llm(message, conversation_history)
    else:
        return generate_agent_response_simple(message, conversation_history)
