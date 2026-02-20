"""
Callback module — sends the final honeypot output to the GUVI evaluation endpoint.
Follows the exact FinalOutput structure from the hackathon spec.
"""
import time
import threading
import requests
from typing import Optional
from models import FinalOutput, SessionData, ExtractedIntelligence


GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
CALLBACK_TIMEOUT = 15  # seconds


def build_final_output(session: SessionData) -> FinalOutput:
    """Build the FinalOutput payload from session data"""
    # Re-extract from full conversation history to ensure nothing is missed
    from extraction import extract_intelligence_from_conversation
    full_intel = extract_intelligence_from_conversation(session.conversationHistory)

    # Merge with any accumulated session intelligence
    from extraction import merge_intelligence
    merged = merge_intelligence(session.extractedIntelligence, full_intel)

    notes = session.agentNotes or "Honeypot engaged scammer successfully."
    if session.scamType:
        notes = f"[{session.scamType.upper()}] {notes}"
    if session.redFlagsFound:
        notes += f" Red flags: {', '.join(session.redFlagsFound[:5])}."

    return FinalOutput(
        sessionId=session.sessionId,
        scamDetected=session.scamDetected,
        totalMessagesExchanged=session.totalMessagesExchanged,
        engagementDurationSeconds=int(time.time() - session.startTime),
        extractedIntelligence=merged,
        agentNotes=notes,
        scamType=session.scamType,
        confidenceLevel=session.confidenceLevel,
    )


def send_callback(session: SessionData) -> tuple:
    """Send the final output to GUVI endpoint. Returns (success, error_msg)."""
    payload = build_final_output(session)

    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload.model_dump(exclude_none=False),
            headers={"Content-Type": "application/json"},
            timeout=CALLBACK_TIMEOUT,
        )
        if response.status_code in (200, 201, 202):
            print(f"✅ Callback sent for session {session.sessionId}: {response.status_code}")
            return True, None
        else:
            msg = f"Callback HTTP {response.status_code}: {response.text[:200]}"
            print(f"❌ {msg}")
            return False, msg

    except requests.exceptions.Timeout:
        msg = f"Callback timeout for {session.sessionId}"
        print(f"❌ {msg}")
        return False, msg
    except requests.exceptions.RequestException as e:
        msg = f"Callback request error: {e}"
        print(f"❌ {msg}")
        return False, msg
    except Exception as e:
        msg = f"Unexpected callback error: {e}"
        print(f"❌ {msg}")
        return False, msg


def try_send_callback(session: SessionData, session_manager) -> bool:
    """
    Attempt to send callback in a background thread if conditions are met.
    Non-blocking so it doesn't delay the API response.
    """
    if not session_manager.should_send_callback(session.sessionId):
        return False

    def _send():
        success, error = send_callback(session)
        if success:
            session_manager.mark_callback_sent(session.sessionId)
        else:
            print(f"⚠️ Callback failed (will retry on next turn): {error}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    return True


def force_send_callback(session: SessionData, session_manager) -> bool:
    """
    Force-send a final callback regardless of message count.
    Used at conversation end (e.g. /final endpoint).
    """
    if session.callbackSent:
        print(f"ℹ️ Callback already sent for {session.sessionId}")
        return True

    success, _ = send_callback(session)
    if success:
        session_manager.mark_callback_sent(session.sessionId)
    return success
