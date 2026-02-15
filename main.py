"""
Main FastAPI application
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
"""
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import HoneypotRequest, HoneypotResponse
from detection import analyze_message
from agent import generate_agent_response
from extraction import extract_intelligence_from_message
from session_manager import session_manager
from callback import try_send_callback

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
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_honeypot_live_a8f92c3e4b5d6789xyz")


@app.get("/")
async def root():
    """Serve the frontend interface"""
    from fastapi.responses import FileResponse
    return FileResponse("index.html")


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
        
        # Detect scam / analyze message
        # Pass current session confidence score to allow cumulative tracking/escalation
        current_score = session.confidenceScore
        new_score, classification, keywords = analyze_message(request.message, full_history, current_score)
        
        # Extract intelligence from message first so agent knows what we have
        new_intelligence = extract_intelligence_from_message(request.message)
        
        # Update session with new data immediately
        # Note: We update confidence and classification
        session = session_manager.update_session(
            request.sessionId,
            new_message=request.message,
            scam_detected=(classification == "scammer"),
            intelligence=new_intelligence,
            agent_notes=f"Keywords: {', '.join(keywords[:5])}" if keywords else None,
            confidence_score=new_score,
            classification=classification
        )
        
        # Use AI agent to generate response (now aware of collected intel and classification)
        current_intel_dict = session.extractedIntelligence.model_dump()
        
        # Pass the new classification and score to the agent
        agent_data = generate_agent_response(
            request.message, 
            full_history, 
            current_intel_dict, 
            classification=classification, 
            confidence_score=new_score
        )
        
        agent_reply = agent_data.get("reply", "I am confused.")
        agent_scam_detected = agent_data.get("scamDetected", False)
        agent_intel = agent_data.get("intelligence", {})
        agent_notes = agent_data.get("agentNotes", "")
        agent_goal = agent_data.get("current_goal", "Engage Scammer")

        # Merge AI-extracted intelligence with regex intelligence
        from extraction import ExtractedIntelligence
        # Convert dict to Pydantic model for merging
        ai_intel_model = ExtractedIntelligence(**agent_intel) if agent_intel else ExtractedIntelligence()
        
        # Merge function (simple union for lists)
        for field in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"]:
            current_list = getattr(new_intelligence, field)
            ai_list = getattr(ai_intel_model, field)
            setattr(new_intelligence, field, list(set(current_list + ai_list)))
            
        # Update keywords if any found by detection
        if keywords:
            new_intelligence.suspiciousKeywords = list(set(new_intelligence.suspiciousKeywords + keywords))

        # Update session AGAIN with AI insights
        session = session_manager.update_session(
            request.sessionId,
            scam_detected=(classification == "scammer") or agent_scam_detected,
            intelligence=new_intelligence,
            agent_notes=agent_notes
        )
        
        # Add agent's response to session history
        from models import Message
        agent_message = Message(
            sender="user",
            text=agent_reply,
            timestamp=request.message.timestamp + 1000
        )
        session_manager.update_session(
            request.sessionId,
            new_message=agent_message
        )
        
        # Check if callback should be sent (only if scam confirmed)
        if session.scamDetected and not session.callbackSent:
             # Basic logic to prevent callback spam, handled inside try_send_callback too
             try_send_callback(session, session_manager)
        
        # Return response including new metrics
        return HoneypotResponse(
            status="success",
            reply=agent_reply,
            scamDetected=session.scamDetected,
            intelligence=new_intelligence.model_dump(),
            sessionId=request.sessionId,
            currentGoal=agent_goal,
            confidenceScore=new_score,
            classification=classification
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
