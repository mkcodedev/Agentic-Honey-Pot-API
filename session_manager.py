"""
Session management module
Handles in-memory storage and tracking of conversation sessions
"""
from typing import Dict, Optional
from models import SessionData, Message, ExtractedIntelligence


class SessionManager:
    """
    In-memory session manager for tracking conversations
    """
    
    def __init__(self):
        """Initialize the session manager with empty storage"""
        self.sessions: Dict[str, SessionData] = {}
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            SessionData if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def create_session(self, session_id: str) -> SessionData:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Newly created SessionData
        """
        session = SessionData(sessionId=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_or_create_session(self, session_id: str) -> SessionData:
        """
        Get existing session or create new one
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Existing or newly created SessionData
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session
    
    def update_session(
        self,
        session_id: str,
        new_message: Optional[Message] = None,
        scam_detected: Optional[bool] = None,
        intelligence: Optional[ExtractedIntelligence] = None,
        agent_notes: Optional[str] = None
    ) -> SessionData:
        """
        Update session data
        
        Args:
            session_id: Unique session identifier
            new_message: New message to add to conversation history
            scam_detected: Whether scam was detected
            intelligence: Extracted intelligence to merge
            agent_notes: Notes about the scammer behavior
            
        Returns:
            Updated SessionData
        """
        session = self.get_or_create_session(session_id)
        
        # Add new message to history
        if new_message:
            session.conversationHistory.append(new_message)
            session.totalMessagesExchanged += 1
        
        # Update scam detection status
        if scam_detected is not None:
            session.scamDetected = scam_detected
        
        # Merge intelligence data
        if intelligence:
            from extraction import merge_intelligence
            session.extractedIntelligence = merge_intelligence(
                session.extractedIntelligence,
                intelligence
            )
        
        # Update agent notes with deduplication
        if agent_notes:
            if not session.agentNotes:
                session.agentNotes = agent_notes
            elif agent_notes not in session.agentNotes:
                # Append new notes only if they contain new information
                session.agentNotes += f" | {agent_notes}"
        
        return session
    
    def mark_callback_sent(self, session_id: str) -> None:
        """
        Mark that callback has been sent for this session
        
        Args:
            session_id: Unique session identifier
        """
        session = self.get_session(session_id)
        if session:
            session.callbackSent = True
    
    def should_send_callback(self, session_id: str) -> bool:
        """
        Check if callback should be sent for this session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if callback should be sent, False otherwise
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Callback should be sent if:
        # 1. Scam was detected
        # 2. At least 8 messages exchanged
        # 3. Callback not already sent
        return (
            session.scamDetected and
            session.totalMessagesExchanged >= 8 and
            not session.callbackSent
        )
    
    def get_session_count(self) -> int:
        """
        Get total number of active sessions
        
        Returns:
            Number of sessions
        """
        return len(self.sessions)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Remove a session from storage
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was removed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def clear_all_sessions(self) -> None:
        """Clear all sessions from storage"""
        self.sessions.clear()


# Global session manager instance
session_manager = SessionManager()
