"""
Main FastAPI application
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
"""
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.models import HoneypotRequest, HoneypotResponse
from src.detection import is_scam
from src.agent import generate_agent_response
from src.extraction import extract_intelligence_from_message
from src.session_manager import session_manager
from src.callback import try_send_callback

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI-powered scam detection and intelligence extraction system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "default-secret-key-change-me")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Agentic Honey-Pot API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "honeypot": "/api/honeypot",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": session_manager.get_session_count()
    }


@app.post("/api/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: str = Header(...)
):
    """
    Main honeypot endpoint for processing scam conversations
    
    Args:
        request: Honeypot request with message and conversation history
        x_api_key: API key for authentication (required in header)
        
    Returns:
        HoneypotResponse with AI-generated reply and scam detection status
        
    Raises:
        HTTPException: 401 if API key is invalid
    """
    # Validate API key
    if x_api_key != HONEYPOT_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.sessionId)
        
        # Add current message to conversation history (for detection)
        full_history = request.conversationHistory + [request.message]
        
        # Detect if message is a scam
        scam_detected, keywords = is_scam(request.message, full_history)
        
        # Update session with scam detection status
        if scam_detected:
            session_manager.update_session(
                request.sessionId,
                scam_detected=True
            )
        
        # Generate agent response
        if scam_detected or session.scamDetected:
            # Use AI agent to generate human-like response
            agent_reply = generate_agent_response(request.message, full_history)
            
            # Extract intelligence from scammer's message
            intelligence = extract_intelligence_from_message(request.message)
            
            # Update session with new message and extracted intelligence
            session_manager.update_session(
                request.sessionId,
                new_message=request.message,
                scam_detected=True,
                intelligence=intelligence,
                agent_notes=f"Keywords detected: {', '.join(keywords[:5])}" if keywords else None
            )
            
            # Add agent's response to session history
            from models import Message
            agent_message = Message(
                sender="user",
                text=agent_reply,
                timestamp=request.message.timestamp + 1
            )
            session_manager.update_session(
                request.sessionId,
                new_message=agent_message
            )
            
            # Check if callback should be sent
            try_send_callback(session, session_manager)
            
            # Return response
            return HoneypotResponse(
                status="success",
                reply=agent_reply,
                scamDetected=True,
                intelligence=intelligence,
                sessionId=request.sessionId
            )
        else:
            # Not a scam - simple acknowledgment
            session_manager.update_session(
                request.sessionId,
                new_message=request.message
            )
            
            return HoneypotResponse(
                status="success",
                reply="Thank you for your message.",
                scamDetected=False,
                intelligence={},
                sessionId=request.sessionId
            )
            
    except Exception as e:
        # Log error and return error response
        print(f"❌ Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "An unexpected error occurred",
            "error": str(exc)
        }
    )


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
    🚀 Starting Agentic Honey-Pot API
    📡 Server: http://0.0.0.0:{port}
    📚 Docs: http://0.0.0.0:{port}/docs
    🔑 API Key Required: {HONEYPOT_API_KEY}
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
