"""
Pydantic models for request/response validation
Covers all fields required by the hackathon evaluation spec
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import time


class Message(BaseModel):
    """Individual message model"""
    sender: str  # "scammer" or "user"
    text: str
    timestamp: Union[int, float] = Field(default_factory=lambda: int(time.time() * 1000))


class Metadata(BaseModel):
    """Metadata for the conversation"""
    channel: str = "SMS"   # SMS, WhatsApp, Email, Chat, etc.
    language: str = "English"
    locale: str = "IN"


class HoneypotRequest(BaseModel):
    """Request model for /api/honeypot endpoint"""
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list)
    metadata: Optional[Metadata] = Field(default_factory=Metadata)


class HoneypotResponse(BaseModel):
    """Response model for /api/honeypot endpoint — returns status + reply"""
    status: str = "success"
    reply: str
    scamDetected: bool = False
    sessionId: str


class ExtractedIntelligence(BaseModel):
    """Structure for extracted scam intelligence — all fields from eval spec"""
    phoneNumbers: List[str] = Field(default_factory=list)
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    emailAddresses: List[str] = Field(default_factory=list)
    caseIds: List[str] = Field(default_factory=list)
    policyNumbers: List[str] = Field(default_factory=list)
    orderNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)


class FinalOutput(BaseModel):
    """
    Final output payload submitted after conversation ends.
    Matches the exact structure from the hackathon evaluation spec.
    """
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    engagementDurationSeconds: int
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agentNotes: str = ""
    scamType: Optional[str] = None
    confidenceLevel: Optional[float] = None


class SessionData(BaseModel):
    """Session data structure for tracking conversations"""
    sessionId: str
    totalMessagesExchanged: int = 0
    engagementDurationSeconds: int = 0
    startTime: float = Field(default_factory=lambda: time.time())
    scamDetected: bool = False
    callbackSent: bool = False
    conversationHistory: List[Message] = Field(default_factory=list)
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agentNotes: str = ""
    scamType: Optional[str] = None
    confidenceLevel: Optional[float] = 1.0
    redFlagsFound: List[str] = Field(default_factory=list)
    questionsAsked: int = 0
    elicitationAttempts: int = 0
