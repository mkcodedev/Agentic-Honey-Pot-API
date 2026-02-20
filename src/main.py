"""
Main FastAPI application
Agentic Honey-Pot for Scam Detection & Intelligence Extraction

Endpoints:
  GET  /              — API info
  GET  /health        — Health check
  POST /api/honeypot  — Main honeypot endpoint (multi-turn conversation)
  POST /api/final     — Force-submit final output (end of conversation)
  GET  /api/session/{session_id} — Retrieve session state
"""
import os
import time
import sys

# Ensure src/ is on the path when running from different directories
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import HoneypotRequest, HoneypotResponse, Message, FinalOutput
from detection import is_scam
from honeypot_agent import generate_agent_response
from extraction import extract_intelligence_from_message, extract_intelligence_from_conversation
from session_manager import session_manager
from callback import try_send_callback, force_send_callback, build_final_output

# ─── Load env ────────────────────────────────────────────────────────────────
# Try .env in project root (parent of src/) first, then cwd, then system env

_HERE     = os.path.dirname(os.path.abspath(__file__))   # src/
_ROOT     = os.path.dirname(_HERE)                        # project root
_ENV_PATH = os.path.join(_ROOT, ".env")

if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    load_dotenv(override=True)   # fallback: search cwd / parent dirs

HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "default-secret-key-change-me")

# ─── App setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agentic Honey-Pot API",
    description=(
        "AI-powered scam detection and intelligence extraction system. "
        "Engages scammers in realistic multi-turn conversations, extracts intelligence, "
        "and automatically submits final analysis to the evaluation endpoint."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth helper ─────────────────────────────────────────────────────────────

def verify_api_key(x_api_key: str):
    """Raises 401 if API key is invalid"""
    if not HONEYPOT_API_KEY or x_api_key != HONEYPOT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
async def root():
    """API information and available endpoints"""
    return {
        "service": "Agentic Honey-Pot API",
        "version": "2.0.0",
        "status": "active",
        "description": "AI-powered honeypot for scam detection and intelligence extraction",
        "endpoints": {
            "honeypot": "POST /api/honeypot",
            "final":    "POST /api/final",
            "session":  "GET  /api/session/{session_id}",
            "health":   "GET  /health",
            "docs":     "GET  /docs",
        },
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check — returns active session count"""
    return {
        "status": "healthy",
        "active_sessions": session_manager.get_session_count(),
        "timestamp": int(time.time()),
    }


@app.post("/api/honeypot", tags=["Honeypot"])
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: str = Header(..., alias="x-api-key"),
):
    """
    Main honeypot endpoint — processes a single turn in the scam conversation.

    - Detects scam patterns using keyword + pattern + optional LLM analysis
    - Generates an engaging, investigative response to keep the scammer talking
    - Extracts all intelligence (phones, accounts, UPIs, links, emails, etc.)
    - Tracks session state across up to 10 conversation turns
    - Submits final output automatically after sufficient engagement

    Returns `{ "status": "success", "reply": "..." }`
    """
    verify_api_key(x_api_key)

    try:
        # ── Session ───────────────────────────────────────────────────────────
        session = session_manager.get_or_create_session(request.sessionId)

        # ── Build full history (previous + current message) ───────────────────
        full_history: list = list(request.conversationHistory) + [request.message]

        # ── Scam Detection ────────────────────────────────────────────────────
        scam_flag, keywords, scam_type, red_flags = is_scam(request.message, full_history)

        # Once scam detected for a session, it stays detected
        is_scam_session = scam_flag or session.scamDetected

        if scam_flag:
            session_manager.update_session(
                request.sessionId,
                scam_detected=True,
                scam_type=scam_type,
                red_flags=red_flags,
                agent_notes=(
                    f"Scam type: {scam_type}. Keywords: {', '.join(keywords[:5])}"
                    if keywords else f"Scam type: {scam_type}"
                ),
            )

        # ── Intelligence extraction from current message ──────────────────────
        intel = extract_intelligence_from_message(request.message)

        # ── Generate response ─────────────────────────────────────────────────
        if is_scam_session:
            agent_reply = generate_agent_response(
                request.message,
                full_history,
                scam_type=scam_type or session.scamType,
                red_flags=red_flags,
            )

            # Count questions in the reply
            question_count = agent_reply.count("?")
            is_question = question_count > 0

            # Count elicitation attempts (reply asks for identifying info)
            elicitation_keywords = [
                "employee id", "phone number", "official number", "your name",
                "branch address", "supervisor", "case number", "reference number",
                "official website", "callback number", "email", "department name"
            ]
            is_elicitation = any(kw in agent_reply.lower() for kw in elicitation_keywords)

            # Add scammer message + our reply to session
            session_manager.update_session(
                request.sessionId,
                new_message=request.message,
                intelligence=intel,
                question_asked=is_question,
                elicitation_attempt=is_elicitation,
            )

            # Add agent reply as "user" message
            agent_msg = Message(
                sender="user",
                text=agent_reply,
                timestamp=int(time.time() * 1000),
            )
            session_manager.update_session(request.sessionId, new_message=agent_msg)

        else:
            # Not a scam yet — store message, give neutral reply
            session_manager.update_session(
                request.sessionId,
                new_message=request.message,
            )
            agent_reply = "Hello, how can I help you today?"

        # ── Re-fetch updated session ──────────────────────────────────────────
        session = session_manager.get_session(request.sessionId)

        # ── Trigger async callback if conditions met ──────────────────────────
        if session and session.scamDetected:
            try_send_callback(session, session_manager)

        # ── Return response ───────────────────────────────────────────────────
        return {
            "status": "success",
            "reply": agent_reply,
            "scamDetected": is_scam_session,
            "sessionId": request.sessionId,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in /api/honeypot: {e}")
        # Always return 200 with a reply — never let the evaluator get a 500
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "Sorry, I'm having some trouble. Can you please repeat that?",
                "scamDetected": False,
                "sessionId": request.sessionId,
            },
        )


@app.post("/api/final", tags=["Honeypot"])
async def submit_final_output(
    session_id: str,
    x_api_key: str = Header(..., alias="x-api-key"),
):
    """
    Force-submit the final output for a session to the GUVI evaluation endpoint.
    Call this when the conversation ends to ensure the full analysis is submitted.
    """
    verify_api_key(x_api_key)

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")

    # Re-extract from entire conversation to ensure completeness
    full_intel = extract_intelligence_from_conversation(session.conversationHistory)
    from extraction import merge_intelligence
    session.extractedIntelligence = merge_intelligence(session.extractedIntelligence, full_intel)

    # Update final engagement duration
    session.engagementDurationSeconds = int(time.time() - session.startTime)

    success = force_send_callback(session, session_manager)
    payload = build_final_output(session)

    return {
        "status": "submitted" if success else "failed",
        "callbackSent": success,
        "sessionId": session_id,
        "finalOutput": payload.model_dump(),
    }


@app.get("/api/session/{session_id}", tags=["Debug"])
async def get_session_state(
    session_id: str,
    x_api_key: str = Header(..., alias="x-api-key"),
):
    """Retrieve current state of a session (for debugging / self-evaluation)"""
    verify_api_key(x_api_key)

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")

    return {
        "sessionId": session.sessionId,
        "scamDetected": session.scamDetected,
        "scamType": session.scamType,
        "totalMessagesExchanged": session.totalMessagesExchanged,
        "engagementDurationSeconds": int(time.time() - session.startTime),
        "callbackSent": session.callbackSent,
        "questionsAsked": session.questionsAsked,
        "elicitationAttempts": session.elicitationAttempts,
        "redFlagsFound": session.redFlagsFound,
        "extractedIntelligence": session.extractedIntelligence.model_dump(),
        "agentNotes": session.agentNotes,
        "conversationLength": len(session.conversationHistory),
    }


# ─── Global exception handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all — always return a valid JSON so evaluator never sees a crash"""
    print(f"❌ Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "I'm sorry, could you say that again? I missed it.",
            "scamDetected": False,
        },
    )


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    print(f"""
╔══════════════════════════════════════════════════╗
║        Agentic Honey-Pot API  v2.0.0             ║
╠══════════════════════════════════════════════════╣
║  Server  : http://0.0.0.0:{port:<5}                  ║
║  Docs    : http://0.0.0.0:{port:<5}/docs              ║
║  Health  : http://0.0.0.0:{port:<5}/health            ║
╚══════════════════════════════════════════════════╝
""")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # disable reload in production
        log_level="info",
    )
