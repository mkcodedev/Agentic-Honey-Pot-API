# 🍯 Agentic Honey-Pot API

> **Hackathon submission** — AI-powered honeypot system for scam detection, intelligence extraction, and multi-turn scammer engagement.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## 📋 Description

This API acts as an **intelligent honeypot** that pretends to be a confused, cooperative victim while:

- 🕵️ **Detecting** scam patterns using multi-layer analysis (keyword + pattern + LLM)
- 💬 **Engaging** scammers in realistic multi-turn conversations to waste their time
- 🔍 **Extracting** all intelligence they unknowingly reveal (phone numbers, UPI IDs, bank accounts, phishing links, emails, case IDs, etc.)
- 📡 **Reporting** findings to the evaluation endpoint automatically

The persona is **Mr. Sharma** — a 68-year-old retired school teacher who is slightly confused, not tech-savvy, but cooperative — designed to keep scammers talking as long as possible.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11) |
| LLM | Google Gemini (gemini-pro) |
| Detection | Keyword matching + Regex patterns + LLM |
| Session Storage | In-memory (Python dict) |
| HTTP | Uvicorn ASGI server |
| Validation | Pydantic v2 |
| Deployment | Railway / Render / Heroku |

---

## 📁 Project Structure

```
Agentic-Honey-Pot-API/
│
├── src/                        # Source code
│   ├── main.py                 # FastAPI app, routing, orchestration
│   ├── models.py               # Pydantic models (request/response/session)
│   ├── detection.py            # Scam detection (keyword + pattern + LLM)
│   ├── honeypot_agent.py       # Response generator (LLM + rule-based)
│   ├── extraction.py           # Intelligence extractor (8 data types)
│   ├── session_manager.py      # In-memory session tracking
│   └── callback.py             # GUVI final output submission
│
├── docs/
│   └── architecture.md         # System architecture documentation
│
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Your actual env (never committed)
├── .gitignore                  # Git ignore rules
├── Procfile                    # Heroku / Railway process file
├── Dockerfile                  # Docker container definition
├── railway.json                # Railway deployment config
├── nixpacks.toml               # Nixpacks build config
├── runtime.txt                 # Python version spec
├── sample_request.json         # Example API request
└── test_api.py                 # API self-test script
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/mkcodedev/Agentic-Honey-Pot-API.git
cd Agentic-Honey-Pot-API
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required — API authentication key
HONEYPOT_API_KEY=your-secret-api-key-here

# LLM Configuration (recommended for best performance)
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key-here

# Server port
PORT=8000
```

> 💡 Get your Gemini API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

### 4. Run the Application

```bash
# From project root
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Or from src/ directory
cd src && python main.py
```

### 5. Verify It's Working

```bash
curl http://localhost:8000/health
# → {"status": "healthy", "active_sessions": 0, "timestamp": ...}
```

---

## 📡 API Endpoints

### `POST /api/honeypot` — Main Honeypot Endpoint

Processes a single turn in the scam conversation.

**Headers:**
```
Content-Type: application/json
x-api-key: your-secret-api-key-here
```

**Request Body:**
```json
{
  "sessionId": "uuid-v4-session-id",
  "message": {
    "sender": "scammer",
    "text": "URGENT: Your SBI account has been compromised. Share OTP immediately.",
    "timestamp": 1708500000000
  },
  "conversationHistory": [],
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
  "reply": "Oh dear, I'm quite confused. Which account exactly? Can you tell me your employee ID so I can verify you are genuine?",
  "scamDetected": true,
  "sessionId": "uuid-v4-session-id"
}
```

---

### `POST /api/final?session_id={id}` — Force Submit Final Output

Force-submits the final analysis to the GUVI evaluation endpoint.

---

### `GET /api/session/{session_id}` — Get Session State

Returns current session state for debugging.

---

### `GET /health` — Health Check

```json
{"status": "healthy", "active_sessions": 2, "timestamp": 1708500000}
```

---

## 🧠 Approach & Strategy

### Scam Detection (3 layers)

1. **Keyword Matching** — 80+ scam-related keywords (urgent, OTP, blocked, verify, etc.)
2. **Pattern Recognition** — Regex for phone numbers, bank accounts, UPI IDs, URLs, emails
3. **LLM Verification** — Google Gemini provides contextual analysis when rule-based is uncertain

Detection triggers on: ≥2 keywords OR any suspicious data pattern OR ≥1 red flag

### Intelligence Extraction (8 data types)

All extracted using robust regex patterns across the **entire conversation history**:

| Type | Pattern |
|------|---------|
| 📞 Phone Numbers | `+91XXXXXXXXXX` or 10-digit |
| 🏦 Bank Accounts | 9-18 digit sequences |
| 💳 UPI IDs | `name@handle` (all major handles) |
| 🔗 Phishing Links | http/https/www + shortened URLs |
| 📧 Email Addresses | Standard email pattern |
| 🆔 Case IDs | `SBI-12345`, `CASE-987654` patterns |
| 📋 Policy Numbers | `POLICY-XXX` patterns |
| 📦 Order Numbers | `ORDER-XXX`, `TXN-XXX` patterns |

### Engagement Strategy (maximises scoring)

The agent responds differently per turn to keep scammers engaged:

| Turn | Strategy | Scoring Benefit |
|------|---------|----------------|
| 1-2 | Confused, asks clarification | Natural start |
| 3-4 | Cooperative, asks investigative Qs | Questions asked score |
| 5-6 | Stalling, references red flags | Red flag score |
| 7+ | Deep probing — demands identity verification | Elicitation score |

**Every reply contains:**
- At least 1 question (question count score)
- A probe for scammer identity/contact info (elicitation score)
- Reference to a red flag when present (red flag score)

### Final Output

Automatically submitted after sufficient conversation OR on `/api/final` call:

```json
{
  "sessionId": "...",
  "scamDetected": true,
  "totalMessagesExchanged": 10,
  "engagementDurationSeconds": 245,
  "extractedIntelligence": {
    "phoneNumbers": ["+91-9876543210"],
    "bankAccounts": ["1234567890123456"],
    "upiIds": ["scammer.fraud@fakebank"],
    "phishingLinks": ["http://malicious-site.com/claim"],
    "emailAddresses": ["scammer@fake.com"],
    "caseIds": ["SBI-12345"],
    "policyNumbers": [],
    "orderNumbers": []
  },
  "agentNotes": "[BANK_FRAUD] Scammer impersonated SBI. Red flags: urgency_pressure, otp_request, authority_impersonation.",
  "scamType": "bank_fraud",
  "confidenceLevel": 1.0
}
```

---

## 🧪 Testing

### Quick Test with cURL

```bash
curl -X POST http://localhost:8000/api/honeypot \
  -H "x-api-key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "URGENT: Your SBI account is blocked. Share OTP to unblock. Call +91-9876543210",
      "timestamp": 1708500000000
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

### Run the Self-Test Script

```bash
python test_api.py
```

---

## 🚀 Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect Railway to your repo
3. Set environment variables in Railway dashboard:
   - `HONEYPOT_API_KEY`
   - `LLM_PROVIDER=gemini`
   - `LLM_API_KEY`
4. Deploy — Railway uses `railway.json` automatically

### Render

**Build Command:** `pip install -r requirements.txt`
**Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

> **Live Deployment:** `https://agentic-honey-pot.up.railway.app`

### Docker

```bash
docker build -t honeypot-api .
docker run -p 8000:8000 --env-file .env honeypot-api
```

---

## 🔒 Security Notes

- Never commit `.env` with real API keys
- Use `.env.example` as a template reference
- All secrets passed via environment variables only
- API key validated on every request via `x-api-key` header

---

## 📊 Scoring Coverage

| Category | Max Points | Implementation |
|----------|-----------|---------------|
| Scam Detection | 20 | Multi-layer detection → `scamDetected: true` |
| Extracted Intelligence | 30 | 8-type regex extraction from full history |
| Turn Count (≥8) | 8 | Engagement strategy keeps conversation going |
| Questions Asked (≥5) | 4 | Every reply has ≥1 question |
| Relevant Questions | 3 | Investigative probes per scam type |
| Red Flag Identification | 8 | `detect_red_flags()` + referenced in replies |
| Information Elicitation | 7 | Every reply probes for identity/contact info |
| Engagement Duration | 4 | Session timer from first message |
| Messages Exchanged | 6 | Strategy designed for ≥10 exchanges |
| Response Structure | 10 | All required + optional fields present |
| **Total** | **100** | |

---

## 🧩 Code Quality

- ✅ No hardcoded test-specific responses
- ✅ Generic detection works for any scam type
- ✅ LLM-powered natural conversation
- ✅ Rule-based fallback for reliability
- ✅ Clean module separation
- ✅ Comprehensive error handling
- ✅ Always returns 200 (never crashes the evaluator)

---

## 📄 License

MIT License — free to use for hackathons and learning.

---

**Made with ❤️ for cybersecurity and scam prevention**
