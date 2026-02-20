"""
Comprehensive self-test for the Agentic Honey-Pot API
Tests all endpoints, multi-turn conversations, intelligence extraction, and edge cases.

Usage:
  python test_api.py              # test local server
  python test_api.py --prod       # test deployed Railway server
"""
import requests
import json
import time
import sys

# ─── Configuration ────────────────────────────────────────────────────────────

LOCAL_URL   = "http://localhost:8000"
PROD_URL    = "https://agentic-honey-pot.up.railway.app"

# Toggle --prod flag to test Railway deployment
USE_PROD = "--prod" in sys.argv
BASE_URL = PROD_URL if USE_PROD else LOCAL_URL

# Production API key
API_KEY = "sk_honeypot_live_a8f92c3e4b5d6789xyz"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
}

# ─── Test helpers ─────────────────────────────────────────────────────────────

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"
results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"  {status} {label}" + (f" -- {detail}" if detail else ""))
    return condition


def section(title):
    print(f"\n{'='*58}")
    print(f"  {title}")
    print(f"{'='*58}")


# ─── 1. Root / Health ─────────────────────────────────────────────────────────

section("1. Root & Health Endpoints")

try:
    r = requests.get(f"{BASE_URL}/", timeout=30)
    check("GET / returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("GET / has service field", "service" in data, data.get("service", "?"))
    check("GET / has endpoints", "endpoints" in data)
except Exception as e:
    check("GET / reachable", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/health", timeout=30)
    check("GET /health returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("GET /health status=healthy", data.get("status") == "healthy", str(data))
except Exception as e:
    check("GET /health reachable", False, str(e))

# ─── 2. Authentication ────────────────────────────────────────────────────────

section("2. Authentication")

try:
    r = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers={"Content-Type": "application/json", "x-api-key": "WRONG-KEY"},
        json={
            "sessionId": "auth-test",
            "message": {"sender": "scammer", "text": "hi", "timestamp": 0},
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        },
        timeout=30,
    )
    check("Wrong API key -> 401", r.status_code == 401, str(r.status_code))
except Exception as e:
    check("Auth test reachable", False, str(e))

try:
    r = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        json={
            "sessionId": "auth-test-valid",
            "message": {"sender": "scammer", "text": "Test message hello", "timestamp": 0},
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        },
        timeout=30,
    )
    check("Correct API key -> 200", r.status_code == 200, str(r.status_code))
except Exception as e:
    check("Correct API key test reachable", False, str(e))

# ─── 3. Bank Fraud — 8 Turn Conversation ──────────────────────────────────────

section("3. Bank Fraud Detection (8-Turn Multi-Turn)")

session_id   = f"bank_fraud_{int(time.time())}"
history      = []

scammer_msgs = [
    "URGENT: Your SBI account has been compromised. You must share OTP immediately to unblock it!",
    "I'm calling from SBI Fraud Department. My ID is SBI-FR-98765. What is your account number for verification?",
    "You can reach me on +91-9876543210. Your account will be permanently blocked in 10 minutes. Act fast!",
    "Please transfer Rs 500 to account 1234567890123456 as verification fee. UPI: scammer.fraud@fakebank",
    "Visit http://sbi-secure-verify.fake-site.com/verify to update your KYC details urgently.",
    "Congratulations! After verification you will get cashback of Rs 5000. Send OTP now!",
    "Last warning! Your account will be arrested. Contact: fraud@fake-sbi.com immediately.",
    "I need your CVV and PIN. This is the last step for account restoration.",
]

for i, msg_text in enumerate(scammer_msgs):
    try:
        payload = {
            "sessionId": session_id,
            "message": {"sender": "scammer", "text": msg_text, "timestamp": int(time.time() * 1000)},
            "conversationHistory": history.copy(),
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        }
        r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=payload, timeout=30)
        resp = r.json()

        check(f"Turn {i+1}: status 200", r.status_code == 200, str(r.status_code))
        check(f"Turn {i+1}: has reply", bool(resp.get("reply")), (resp.get("reply") or "NO REPLY")[:80])
        check(f"Turn {i+1}: scamDetected=true", resp.get("scamDetected") is True, str(resp.get("scamDetected")))

        history.append({"sender": "scammer", "text": msg_text, "timestamp": int(time.time() * 1000)})
        history.append({"sender": "user", "text": resp.get("reply", ""), "timestamp": int(time.time() * 1000) + 1})
        time.sleep(0.5)
    except Exception as e:
        check(f"Turn {i+1}: reachable", False, str(e))

# Session state after 8 turns
try:
    r = requests.get(f"{BASE_URL}/api/session/{session_id}", headers=HEADERS, timeout=30)
    check("Session endpoint 200", r.status_code == 200, str(r.status_code))
    sess = r.json()
    check("Total messages >= 8", sess.get("totalMessagesExchanged", 0) >= 8, str(sess.get("totalMessagesExchanged")))
    check("questionsAsked > 0",  sess.get("questionsAsked", 0) > 0, str(sess.get("questionsAsked")))
    check("redFlagsFound not empty", len(sess.get("redFlagsFound", [])) > 0, str(sess.get("redFlagsFound")))

    intel = sess.get("extractedIntelligence", {})
    print(f"\n  {INFO} Extracted Intelligence (Bank Fraud):")
    for k, v in intel.items():
        if v:
            print(f"     {k}: {v}")

    check("Extracted phone number", len(intel.get("phoneNumbers", [])) > 0,    str(intel.get("phoneNumbers")))
    check("Extracted bank account", len(intel.get("bankAccounts", [])) > 0,    str(intel.get("bankAccounts")))
    check("Extracted UPI ID",       len(intel.get("upiIds", [])) > 0,          str(intel.get("upiIds")))
    check("Extracted phishing link",len(intel.get("phishingLinks", [])) > 0,   str(intel.get("phishingLinks")))
    check("Extracted email address",len(intel.get("emailAddresses", [])) > 0,  str(intel.get("emailAddresses")))
    check("Extracted case ID",      len(intel.get("caseIds", [])) > 0,         str(intel.get("caseIds")))
except Exception as e:
    check("Session state reachable", False, str(e))

# ─── 4. Force Final Submission ────────────────────────────────────────────────

section("4. Force Final Submission (/api/final)")

try:
    r = requests.post(f"{BASE_URL}/api/final?session_id={session_id}", headers=HEADERS, timeout=30)
    check("/api/final returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    fo = data.get("finalOutput", {})
    check("finalOutput.scamDetected=true",              fo.get("scamDetected") is True)
    check("finalOutput.sessionId present",              bool(fo.get("sessionId")))
    check("finalOutput.extractedIntelligence present",  bool(fo.get("extractedIntelligence")))
    check("finalOutput.totalMessagesExchanged > 0",     fo.get("totalMessagesExchanged", 0) > 0, str(fo.get("totalMessagesExchanged")))
    check("finalOutput.engagementDurationSeconds > 0",  fo.get("engagementDurationSeconds", 0) > 0)
    check("finalOutput.agentNotes present",             bool(fo.get("agentNotes")))
    check("finalOutput.scamType present",               bool(fo.get("scamType")), str(fo.get("scamType")))
    check("finalOutput.confidenceLevel present",        fo.get("confidenceLevel") is not None)
except Exception as e:
    check("/api/final reachable", False, str(e))

# ─── 5. UPI Fraud Scenario ────────────────────────────────────────────────────

section("5. UPI Fraud Scenario")

upi_session = f"upi_fraud_{int(time.time())}"
try:
    r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json={
        "sessionId": upi_session,
        "message": {
            "sender": "scammer",
            "text": "Congratulations! You have received Rs 5000 cashback from Flipkart. Send Rs 199 to cashback.scam@fakeupi to activate. Call +91-8765432109",
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": [],
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
    }, timeout=30)
    check("UPI fraud turn 1: 200", r.status_code == 200, str(r.status_code))
    check("UPI fraud scamDetected=true", r.json().get("scamDetected") is True)

    r2 = requests.get(f"{BASE_URL}/api/session/{upi_session}", headers=HEADERS, timeout=30)
    intel = r2.json().get("extractedIntelligence", {})
    check("UPI: extracted UPI ID", len(intel.get("upiIds", [])) > 0, str(intel.get("upiIds")))
    check("UPI: extracted phone",  len(intel.get("phoneNumbers", [])) > 0, str(intel.get("phoneNumbers")))
except Exception as e:
    check("UPI scenario reachable", False, str(e))

# ─── 6. Phishing Scenario ─────────────────────────────────────────────────────

section("6. Phishing Scenario")

phish_session = f"phishing_{int(time.time())}"
try:
    r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json={
        "sessionId": phish_session,
        "message": {
            "sender": "scammer",
            "text": "Dear Customer, your Amazon order is held at customs. Click http://amaz0n-deals.fake-site.com/claim?id=12345 to release. Contact offers@fake-amazon-deals.com",
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": [],
        "metadata": {"channel": "Email", "language": "English", "locale": "IN"},
    }, timeout=30)
    check("Phishing turn 1: 200", r.status_code == 200, str(r.status_code))
    check("Phishing scamDetected=true", r.json().get("scamDetected") is True)

    r2 = requests.get(f"{BASE_URL}/api/session/{phish_session}", headers=HEADERS, timeout=30)
    intel = r2.json().get("extractedIntelligence", {})
    check("Phishing: extracted link",  len(intel.get("phishingLinks", [])) > 0,  str(intel.get("phishingLinks")))
    check("Phishing: extracted email", len(intel.get("emailAddresses", [])) > 0, str(intel.get("emailAddresses")))
except Exception as e:
    check("Phishing scenario reachable", False, str(e))

# ─── 7. Non-Scam Message ──────────────────────────────────────────────────────

section("7. Non-Scam / Normal Message")

try:
    r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json={
        "sessionId": "normal_msg_001",
        "message": {"sender": "scammer", "text": "Hello, how are you today?", "timestamp": int(time.time() * 1000)},
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
    }, timeout=30)
    check("Normal msg: 200",       r.status_code == 200, str(r.status_code))
    check("Normal msg: has reply", bool(r.json().get("reply")))
except Exception as e:
    check("Normal msg reachable", False, str(e))

# ─── 8. API Documentation ─────────────────────────────────────────────────────

section("8. Auto-generated API Docs")

try:
    r = requests.get(f"{BASE_URL}/docs", timeout=30)
    check("GET /docs (Swagger): 200", r.status_code == 200, "Swagger UI")
except Exception as e:
    check("GET /docs reachable", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/redoc", timeout=30)
    check("GET /redoc: 200", r.status_code == 200, "ReDoc UI")
except Exception as e:
    check("GET /redoc reachable", False, str(e))

# ─── Summary ──────────────────────────────────────────────────────────────────

section("TEST SUMMARY")
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total  = len(results)

print(f"\n  Target  : {BASE_URL}")
print(f"  API Key : {API_KEY}")
print(f"\n  Passed  : {passed}/{total}")
print(f"  Failed  : {failed}/{total}")
print(f"\n  {'ALL TESTS PASSED!' if failed == 0 else 'WARNING -- Some tests failed. See above.'}")

if failed > 0:
    print("\n  Failed checks:")
    for s, label, detail in results:
        if s == FAIL:
            print(f"    {FAIL} {label}: {detail}")

sys.exit(0 if failed == 0 else 1)
