# 🍯 Agentic Honey-Pot for Scam Detection & Intelligence Extraction

A production-ready Python FastAPI backend that uses AI agents to detect scams, engage with scammers in multi-turn conversations, extract intelligence, and automatically report findings to evaluation endpoints.

## 🎯 Core Features

- **✅ Scam Detection**: Keyword-based + optional LLM-powered detection
- **🤖 AI Agent**: Autonomous conversational agent that mimics confused but cooperative human behavior
- **💬 Multi-Turn Conversations**: Tracks session history and context across messages
- **🔍 Intelligence Extraction**: Automatically extracts bank accounts, UPI IDs, phone numbers, URLs, and suspicious keywords
- **📡 Automatic Callbacks**: Sends final results to GUVI evaluation endpoint after 8+ messages
- **🔐 API Key Authentication**: Secure REST API with header-based authentication
- **📊 Session Management**: In-memory tracking of conversation state

---

## 📁 Project Structure

```
agentic-honeypot/
│
├── main.py                 # FastAPI application entry point
├── models.py               # Pydantic models for validation
├── detection.py            # Scam detection logic (keyword + LLM)
├── agent.py                # AI agent conversation generator
├── extraction.py           # Intelligence extraction (regex-based)
├── session_manager.py      # In-memory session tracking
├── callback.py             # GUVI endpoint callback handler
│
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update with your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Required
HONEYPOT_API_KEY=your-secret-api-key-here

# Optional (for LLM-based detection and responses)
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key-here

# Server
PORT=8000
```

### 3. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Base**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 📡 API Usage

### POST `/api/honeypot`

Main endpoint for processing scam conversations.

**Headers:**
```
x-api-key: your-secret-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your bank account has been suspended. Verify now by sending OTP to 9876543210",
    "timestamp": 1770005528731
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Hello, this is from State Bank",
      "timestamp": 1770005528731
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "Oh no! What OTP? I haven't received any message. What should I do?",
  "scamDetected": true,
  "sessionId": "unique-session-id"
}
```

---

## 🔍 How It Works

### 1. **Scam Detection**

The system uses multiple detection methods:

- **Keyword Matching**: Detects 50+ scam-related keywords (urgent, verify, OTP, blocked, etc.)
- **Pattern Recognition**: Identifies suspicious patterns (account numbers, UPI IDs, URLs)
- **Optional LLM**: Uses Google Gemini for context-aware detection

**Trigger**: 2+ keywords or 1+ suspicious pattern

### 2. **AI Agent Response**

When a scam is detected:

- **Personas**: Confused, cooperative, elderly, or not tech-savvy
- **Strategies**: 
  - Messages 1-2: Show confusion, ask for clarification
  - Messages 3-4: Be cooperative, ask questions
  - Messages 5-6: Stall for time
  - Messages 7+: Ask specific questions to extract info

- **LLM Mode** (optional): Uses Google Gemini for natural human-like responses
- **Rule-Based Mode**: Uses pre-defined templates for fast, reliable responses

### 3. **Intelligence Extraction**

Automatically extracts:

- **Bank Accounts**: 9-18 digit numbers
- **UPI IDs**: `something@paytm`, `name@phonepe`, etc.
- **Phone Numbers**: `+91XXXXXXXXXX` or 10-digit numbers
- **URLs**: `http://`, `https://`, `www.`, shortened links
- **Suspicious Keywords**: OTP, PIN, CVV, urgent, verify, etc.

### 4. **Automatic Callback**

**Trigger Conditions:**
- ✅ Scam detected
- ✅ 8+ messages exchanged
- ✅ Intelligence extracted
- ✅ Callback not yet sent

**Sends to:**
```
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

**Payload:**
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 10,
  "extractedIntelligence": {
    "bankAccounts": ["123456789012"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["http://fake-bank.com"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "otp", "verify"]
  },
  "agentNotes": "Scammer impersonating bank, requesting OTP and account details"
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HONEYPOT_API_KEY` | Yes | `default-secret-key-change-me` | API key for authentication |
| `LLM_PROVIDER` | No | - | Set to `gemini` to enable LLM features |
| `LLM_API_KEY` | No | - | Google Gemini API key |
| `PORT` | No | `8000` | Server port |

### Getting Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key to `.env` file

---

## 🧪 Testing

### Sample cURL Request

```bash
curl -X POST http://localhost:8000/api/honeypot \
  -H "x-api-key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Your account will be blocked. Send OTP immediately to verify.",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🚢 Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect to [Render](https://render.com)
3. Create new Web Service
4. Set environment variables
5. Deploy!

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Deploy to Railway

1. Push code to GitHub
2. Connect to [Railway](https://railway.app)
3. Add environment variables
4. Deploy automatically

### Deploy to Heroku

```bash
# Add Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
git push heroku main
heroku config:set HONEYPOT_API_KEY=your-key
```

---

## 📊 API Response Codes

| Code | Meaning |
|------|---------|
| `200` | Success - message processed |
| `401` | Unauthorized - invalid API key |
| `422` | Validation Error - invalid request format |
| `500` | Internal Server Error |

---

## 🛡️ Security Best Practices

1. **Never commit `.env`** - Use `.env.example` as template
2. **Use strong API keys** - Generate random, long keys
3. **Enable HTTPS** - Always use SSL in production
4. **Rate limiting** - Add rate limiting middleware for production
5. **Monitor logs** - Track suspicious API usage

---

## 🧩 Extending the System

### Add New Scam Keywords

Edit `detection.py`:

```python
SCAM_KEYWORDS = [
    # Add your keywords
    "new_keyword",
    "another_pattern"
]
```

### Add New Agent Responses

Edit `agent.py`:

```python
CUSTOM_RESPONSES = [
    "Your custom response here",
    "Another response template"
]
```

### Add New Extraction Patterns

Edit `extraction.py`:

```python
def extract_custom_data(text: str) -> Set[str]:
    pattern = r'your-regex-pattern'
    return set(re.findall(pattern, text))
```

---

## 🐛 Troubleshooting

### Issue: "Invalid API key"
**Solution**: Check that `x-api-key` header matches `HONEYPOT_API_KEY` in `.env`

### Issue: LLM not working
**Solution**: 
- Verify `LLM_PROVIDER=gemini` in `.env`
- Check `LLM_API_KEY` is valid
- Install: `pip install google-generativeai`

### Issue: Callback not sending
**Solution**:
- Ensure 8+ messages exchanged
- Check `scamDetected=true`
- Verify internet connection
- Check GUVI endpoint is accessible

---

## 📝 License

MIT License - Feel free to use for hackathons and learning!

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📧 Support

For issues or questions:
- Open a GitHub issue
- Check API docs at `/docs` endpoint
- Review logs for error messages

---

## 🎉 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Google Gemini](https://ai.google.dev/) - Optional LLM capabilities

---

**Made with ❤️ for cybersecurity and scam prevention**
