"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Message(BaseModel):
    """Individual message model"""
    sender: Literal["scammer", "user"]
    text: str
    timestamp: int


class Metadata(BaseModel):
    """Metadata for the conversation"""
    channel: Literal["SMS", "WhatsApp", "Email", "Chat"]
    language: str = "English"
    locale: str = "IN"


class HoneypotRequest(BaseModel):
    """Request model for /api/honeypot endpoint"""
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list)
    metadata: Metadata


class ExtractedIntelligence(BaseModel):
    """Structure for extracted scam intelligence"""
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)


class HoneypotResponse(BaseModel):
    """Response model for /api/honeypot endpoint"""
    status: Literal["success", "error"]
    reply: str
    scamDetected: bool
    sessionId: str
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)


class CallbackPayload(BaseModel):
    """Payload for final callback to GUVI endpoint"""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str


class SessionData(BaseModel):
    """Session data structure for tracking conversations"""
    sessionId: str
    totalMessagesExchanged: int = 0
    scamDetected: bool = False
    callbackSent: bool = False
    conversationHistory: List[Message] = Field(default_factory=list)
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agentNotes: str = ""
