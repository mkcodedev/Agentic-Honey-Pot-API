# 📖 Quick Reference Guide

## Essential Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit environment variables
# Windows: notepad .env
# Mac/Linux: nano .env
```

### Run Server
```bash
# Development mode (auto-reload)
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# With multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing
```bash
# Run test suite
python test_api.py

# Test health check
curl http://localhost:8000/health

# Test with sample request
curl -X POST http://localhost:8000/api/honeypot \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | ❌ No | API information |
| GET | `/health` | ❌ No | Health check |
| GET | `/docs` | ❌ No | Interactive API docs |
| POST | `/api/honeypot` | ✅ Yes | Main scam detection endpoint |

---

## Request Format

### Headers
```
x-api-key: your-secret-key
Content-Type: application/json
```

### Body Schema
```json
{
  "sessionId": "string (required)",
  "message": {
    "sender": "scammer | user (required)",
    "text": "string (required)",
    "timestamp": "integer (required)"
  },
  "conversationHistory": [
    {
      "sender": "scammer | user",
      "text": "string",
      "timestamp": "integer"
    }
  ],
  "metadata": {
    "channel": "SMS | WhatsApp | Email | Chat",
    "language": "string (default: English)",
    "locale": "string (default: IN)"
  }
}
```

---

## Response Format

### Success Response
```json
{
  "status": "success",
  "reply": "AI-generated human-like response",
  "scamDetected": true,
  "sessionId": "abc123-session-id"
}
```

### Error Response (401)
```json
{
  "detail": "Invalid API key"
}
```

### Error Response (500)
```json
{
  "status": "error",
  "detail": "Error message",
  "error": "Detailed error"
}
```

---

## Scam Detection Triggers

### Keyword-Based (2+ keywords required)
- Urgency: urgent, immediately, expire, deadline
- Verification: verify, confirm, suspended, blocked
- Financial: upi, account, otp, pin, cvv
- Authority: bank, rbi, police, government
- Threats: arrest, legal action, penalty, fine

### Pattern-Based (any pattern triggers)
- Bank account: 9-18 digit numbers
- UPI IDs: something@paytm, name@phonepe
- Phone numbers: +91XXXXXXXXXX or 10 digits
- URLs: http://, https://, www., bit.ly

---

## Intelligence Extraction

### Automatically Extracts
1. **Bank Accounts**: `\b\d{9,18}\b`
2. **UPI IDs**: `[\w\.-]+@(paytm|phonepe|googlepay|ybl|upi)`
3. **Phone Numbers**: `(\+91[\s-]?)?[6-9]\d{9}`
4. **URLs**: `https?://\S+` or `www\.\S+`
5. **Keywords**: 50+ suspicious terms

---

## Agent Behavior Strategy

| Messages | Strategy | Example Response |
|----------|----------|------------------|
| 1-2 | Confusion | "I'm not sure I understand. Can you explain?" |
| 3-4 | Cooperative questioning | "What information do you need from me?" |
| 5-6 | Stalling | "Let me check... Can you hold on?" |
| 7+ | Specific questions | "Should I share my account number?" |

---

## Callback Trigger Conditions

Callback is sent when **ALL** conditions are met:

- ✅ `scamDetected == true`
- ✅ `totalMessagesExchanged >= 8`
- ✅ `callbackSent == false`
- ✅ Intelligence extracted (any data)

### Callback Endpoint
```
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

### Callback Payload
```json
{
  "sessionId": "string",
  "scamDetected": true,
  "totalMessagesExchanged": 10,
  "extractedIntelligence": {
    "bankAccounts": ["123456789012"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["http://fake.com"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "otp"]
  },
  "agentNotes": "Summary of scammer behavior"
}
```

---

## Configuration Options

### Rule-Based Mode (No LLM)
```bash
# .env
HONEYPOT_API_KEY=your-key
# Leave LLM_PROVIDER empty
```

**Pros**: Fast, free, reliable  
**Cons**: Less natural responses

### LLM Mode (With Gemini)
```bash
# .env
HONEYPOT_API_KEY=your-key
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-key
```

**Pros**: Natural, context-aware responses  
**Cons**: Requires API key, slight latency

---

## Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | ✅ All good |
| 401 | Unauthorized | Check `x-api-key` header |
| 422 | Validation Error | Check request JSON format |
| 500 | Server Error | Check logs for details |

---

## Development Tips

### View All Sessions
```python
# In Python console
from session_manager import session_manager
print(f"Active sessions: {session_manager.get_session_count()}")
print(session_manager.sessions)
```

### Clear All Sessions
```python
from session_manager import session_manager
session_manager.clear_all_sessions()
```

### Test Scam Detection
```python
from detection import is_scam
from models import Message

msg = Message(sender="scammer", text="URGENT! Verify OTP now!", timestamp=123)
scam_detected, keywords = is_scam(msg, [])
print(f"Scam: {scam_detected}, Keywords: {keywords}")
```

### Test Intelligence Extraction
```python
from extraction import extract_intelligence_from_message
from models import Message

msg = Message(sender="scammer", text="Send to 9876543210 or user@paytm", timestamp=123)
intel = extract_intelligence_from_message(msg)
print(intel)
```

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Cold start | ~2s |
| Avg response time (rule-based) | ~50-100ms |
| Avg response time (LLM) | ~1-3s |
| Requests per second | ~100+ (single worker) |
| Memory usage | ~100-150MB |

---

## File Structure Overview

```
scamhot/
├── main.py              # FastAPI app & endpoints
├── models.py            # Pydantic validation models
├── detection.py         # Scam detection logic
├── agent.py             # AI agent responses
├── extraction.py        # Intelligence extraction
├── session_manager.py   # Session tracking
├── callback.py          # GUVI callback handler
├── requirements.txt     # Dependencies
├── .env.example         # Config template
├── README.md            # Main documentation
├── DEPLOYMENT.md        # Deployment guide
├── QUICK_REFERENCE.md   # This file
├── test_api.py          # Test suite
├── sample_request.json  # Example request
├── start.bat            # Windows startup
└── start.sh             # Linux/Mac startup
```

---

## Useful Links

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Google Gemini**: https://ai.google.dev/
- **Uvicorn Docs**: https://www.uvicorn.org/

---

## Support & Debugging

### Enable Debug Mode
```python
# In main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs
```bash
# Server logs
python main.py

# Or with uvicorn
uvicorn main:app --log-level debug
```

### Common Issues

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Connection refused"**
```bash
# Check server is running
curl http://localhost:8000/health
```

**"Invalid API key"**
```bash
# Check .env file exists and has correct key
cat .env
```

---

**Keep this handy for quick reference! 📌**
