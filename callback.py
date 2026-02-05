"""
Callback module for sending final results to GUVI endpoint
"""
import requests
from typing import Optional
from models import CallbackPayload, SessionData


GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
CALLBACK_TIMEOUT = 10  # seconds


def send_callback(session: SessionData) -> tuple[bool, Optional[str]]:
    """
    Send final callback to GUVI endpoint
    
    Args:
        session: Session data to send
        
    Returns:
        Tuple of (success, error_message)
    """
    # Prepare callback payload
    payload = CallbackPayload(
        sessionId=session.sessionId,
        scamDetected=session.scamDetected,
        totalMessagesExchanged=session.totalMessagesExchanged,
        extractedIntelligence=session.extractedIntelligence,
        agentNotes=session.agentNotes or "Scammer engaged successfully"
    )
    
    try:
        # Send POST request to GUVI endpoint
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload.model_dump(),
            headers={
                "Content-Type": "application/json"
            },
            timeout=CALLBACK_TIMEOUT
        )
        
        # Check if request was successful
        if response.status_code in [200, 201, 202]:
            print(f"✅ Callback sent successfully for session {session.sessionId}")
            return True, None
        else:
            error_msg = f"Callback failed with status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = f"Callback timeout for session {session.sessionId}"
        print(f"❌ {error_msg}")
        return False, error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Callback request failed: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error during callback: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg


def try_send_callback(session: SessionData, session_manager) -> bool:
    """
    Attempt to send callback if conditions are met
    
    Args:
        session: Session data
        session_manager: SessionManager instance to update callback status
        
    Returns:
        True if callback was sent, False otherwise
    """
    # Check if callback should be sent
    if not session_manager.should_send_callback(session.sessionId):
        return False
    
    # Send callback
    success, error = send_callback(session)
    
    # Mark callback as sent if successful
    if success:
        session_manager.mark_callback_sent(session.sessionId)
        return True
    else:
        # Log error but don't retry automatically
        print(f"⚠️ Callback failed but will not retry: {error}")
        return False
