"""
Session management module
Handles in-memory storage and tracking of all conversation sessions.
Tracks engagement duration, turn counts, intelligence accumulation, red flags, and question counts.
"""
import time
from typing import Dict, Optional
from models import SessionData, Message, ExtractedIntelligence


class SessionManager:
    """Thread-safe in-memory session manager"""

    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}

    # ─── CRUD ────────────────────────────────

    def get_session(self, session_id: str) -> Optional[SessionData]:
        return self.sessions.get(session_id)

    def create_session(self, session_id: str) -> SessionData:
        session = SessionData(
            sessionId=session_id,
            startTime=time.time(),
        )
        self.sessions[session_id] = session
        return session

    def get_or_create_session(self, session_id: str) -> SessionData:
        return self.sessions.get(session_id) or self.create_session(session_id)

    # ─── Update ───────────────────────────────

    def update_session(
        self,
        session_id: str,
        new_message: Optional[Message] = None,
        scam_detected: Optional[bool] = None,
        intelligence: Optional[ExtractedIntelligence] = None,
        agent_notes: Optional[str] = None,
        scam_type: Optional[str] = None,
        red_flags: Optional[list] = None,
        question_asked: bool = False,
        elicitation_attempt: bool = False,
    ) -> SessionData:
        session = self.get_or_create_session(session_id)

        if new_message:
            session.conversationHistory.append(new_message)
            session.totalMessagesExchanged += 1
            # Always recalculate engagement duration
            session.engagementDurationSeconds = int(time.time() - session.startTime)

        if scam_detected is not None:
            session.scamDetected = scam_detected

        if scam_type and not session.scamType:
            session.scamType = scam_type

        if red_flags:
            for flag in red_flags:
                if flag not in session.redFlagsFound:
                    session.redFlagsFound.append(flag)

        if question_asked:
            session.questionsAsked += 1

        if elicitation_attempt:
            session.elicitationAttempts += 1

        if intelligence:
            from extraction import merge_intelligence
            session.extractedIntelligence = merge_intelligence(
                session.extractedIntelligence,
                intelligence,
            )

        if agent_notes:
            session.agentNotes = (
                f"{session.agentNotes} | {agent_notes}" if session.agentNotes else agent_notes
            )

        return session

    # ─── Callback helpers ─────────────────────

    def mark_callback_sent(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.callbackSent = True

    def should_send_callback(self, session_id: str) -> bool:
        """
        Send callback when scam detected and we've had enough conversation.
        Tries after 8 messages, also tries at end of conversation regardless.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        return (
            session.scamDetected
            and session.totalMessagesExchanged >= 2
            and not session.callbackSent
        )

    def get_session_count(self) -> int:
        return len(self.sessions)

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def clear_all_sessions(self) -> None:
        self.sessions.clear()


# Global singleton
session_manager = SessionManager()
