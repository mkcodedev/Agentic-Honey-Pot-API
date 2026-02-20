"""
Comprehensive self-test for the Agentic Honey-Pot API
Tests all endpoints, multi-turn conversations, intelligence extraction, and edge cases.
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
}

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"  {status} {label}" + (f" — {detail}" if detail else ""))
    return condition

def section(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}")

# ─── 1. Root / Health ─────────────────────────────────────
section("1. Root & Health Endpoints")

r = requests.get(f"{BASE_URL}/")
check("GET / returns 200", r.status_code == 200)
data = r.json()
check("GET / has service field", "service" in data, data.get("service","?"))
check("GET / has endpoints", "endpoints" in data)

r = requests.get(f"{BASE_URL}/health")
check("GET /health returns 200", r.status_code == 200)
data = r.json()
check("GET /health has status:healthy", data.get("status") == "healthy", str(data))

# ─── 2. Auth ──────────────────────────────────────────────
section("2. Authentication")

r = requests.post(f"{BASE_URL}/api/honeypot",
    headers={"Content-Type":"application/json","x-api-key":"WRONG"},
    json={"sessionId":"test","message":{"sender":"scammer","text":"hi","timestamp":0},"metadata":{"channel":"SMS","language":"English","locale":"IN"}}
)
check("Wrong API key → 401", r.status_code == 401, str(r.status_code))

# ─── 3. Bank Fraud Detection ─────────────────────────────
section("3. Bank Fraud Detection (Turn-by-Turn)")

session_id = f"bank_fraud_{int(time.time())}"
history = []
bank_payload = {
    "sessionId": session_id,
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}

scammer_msgs = [
    "URGENT: Your SBI account has been compromised. You must share OTP immediately to unblock it!",
    "I'm calling from SBI Fraud Department. My ID is SBI-FR-98765. What is your account number for verification?",
    "You can reach me on +91-9876543210. Your account will be permanently blocked in 10 minutes. Act fast!",
    "Please transfer Rs 500 to this account 1234567890123456 as verification fee. UPI ID: scammer.fraud@fakebank",
    "Visit http://sbi-secure-verify.fake-site.com/verify to update your KYC details urgently.",
    "Congratulations! After verification you will get a cashback of Rs 5000. Send OTP: 123456 now!",
    "Last warning! Your account will be arrested. Contact our office email: fraud@fake-sbi.com immediately.",
    "I need your CVV and PIN. This is the last step for account restoration. Trust me.",
]

for i, msg_text in enumerate(scammer_msgs):
    payload = dict(bank_payload)
    payload["message"] = {"sender": "scammer", "text": msg_text, "timestamp": int(time.time()*1000)}
    payload["conversationHistory"] = history.copy()

    r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=payload)
    resp = r.json()

    check(f"Turn {i+1}: status 200", r.status_code == 200, f"Got {r.status_code}")
    check(f"Turn {i+1}: has reply", bool(resp.get("reply")), resp.get("reply","NO REPLY")[:80])
    check(f"Turn {i+1}: scamDetected=true", resp.get("scamDetected") == True, str(resp.get("scamDetected")))

    history.append({"sender": "scammer", "text": msg_text, "timestamp": int(time.time()*1000)})
    history.append({"sender": "user", "text": resp.get("reply",""), "timestamp": int(time.time()*1000)+1})
    time.sleep(0.3)

# Check session state
r = requests.get(f"{BASE_URL}/api/session/{session_id}", headers=HEADERS)
check("Session endpoint returns 200", r.status_code == 200)
sess = r.json()
check("Session has questionsAsked>0", sess.get("questionsAsked",0) > 0, str(sess.get("questionsAsked")))
check("Session has redFlagsFound", len(sess.get("redFlagsFound",[])) > 0, str(sess.get("redFlagsFound")))
check("Session totalMessages≥8", sess.get("totalMessagesExchanged",0) >= 8, str(sess.get("totalMessagesExchanged")))

intel = sess.get("extractedIntelligence", {})
print(f"\n  {INFO} Extracted Intelligence:")
print(f"     phoneNumbers   : {intel.get('phoneNumbers', [])}")
print(f"     bankAccounts   : {intel.get('bankAccounts', [])}")
print(f"     upiIds         : {intel.get('upiIds', [])}")
print(f"     phishingLinks  : {intel.get('phishingLinks', [])}")
print(f"     emailAddresses : {intel.get('emailAddresses', [])}")
print(f"     caseIds        : {intel.get('caseIds', [])}")

check("Extracted phone number", len(intel.get("phoneNumbers",[])) > 0, str(intel.get("phoneNumbers")))
check("Extracted bank account", len(intel.get("bankAccounts",[])) > 0, str(intel.get("bankAccounts")))
check("Extracted UPI ID", len(intel.get("upiIds",[])) > 0, str(intel.get("upiIds")))
check("Extracted phishing link", len(intel.get("phishingLinks",[])) > 0, str(intel.get("phishingLinks")))
check("Extracted email address", len(intel.get("emailAddresses",[])) > 0, str(intel.get("emailAddresses")))

# ─── 4. Force Final Submission ───────────────────────────
section("4. Force Final Submission (/api/final)")

r = requests.post(f"{BASE_URL}/api/final?session_id={session_id}", headers=HEADERS)
check("POST /api/final returns 200", r.status_code == 200, str(r.status_code))
data = r.json()
check("Final has finalOutput", "finalOutput" in data, str(list(data.keys())))
fo = data.get("finalOutput", {})
check("finalOutput.scamDetected=true", fo.get("scamDetected") == True)
check("finalOutput.sessionId present", bool(fo.get("sessionId")))
check("finalOutput.extractedIntelligence present", bool(fo.get("extractedIntelligence")))
check("finalOutput.totalMessagesExchanged>0", fo.get("totalMessagesExchanged",0) > 0)
check("finalOutput.engagementDurationSeconds>0", fo.get("engagementDurationSeconds",0) > 0)
check("finalOutput.agentNotes present", bool(fo.get("agentNotes")))
check("finalOutput.scamType present", bool(fo.get("scamType")), fo.get("scamType","?"))
check("finalOutput.confidenceLevel present", fo.get("confidenceLevel") is not None)

# ─── 5. UPI Fraud Scenario ───────────────────────────────
section("5. UPI Fraud Scenario")

upi_session = f"upi_fraud_{int(time.time())}"
upi_msg = {
    "sessionId": upi_session,
    "message": {
        "sender": "scammer",
        "text": "Congratulations! You've received ₹5000 cashback from Flipkart. Send Rs 199 to cashback.scam@fakeupi to activate. Call +91-8765432109",
        "timestamp": int(time.time()*1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"}
}
r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=upi_msg)
check("UPI fraud turn 1 returns 200", r.status_code == 200)
resp = r.json()
check("UPI fraud scamDetected=true", resp.get("scamDetected") == True, str(resp.get("scamDetected")))
check("UPI fraud reply not empty", bool(resp.get("reply")), resp.get("reply","")[:80])

r = requests.get(f"{BASE_URL}/api/session/{upi_session}", headers=HEADERS)
intel = r.json().get("extractedIntelligence", {})
check("UPI: extracted UPI ID", len(intel.get("upiIds",[])) > 0, str(intel.get("upiIds")))
check("UPI: extracted phone", len(intel.get("phoneNumbers",[])) > 0, str(intel.get("phoneNumbers")))

# ─── 6. Phishing Scenario ────────────────────────────────
section("6. Phishing Scenario")

phish_session = f"phishing_{int(time.time())}"
phish_msg = {
    "sessionId": phish_session,
    "message": {
        "sender": "scammer",
        "text": "Dear Customer, your Amazon order is held. Click http://amaz0n-deals.fake-site.com/claim?id=12345 to release. Contact offers@fake-amazon-deals.com",
        "timestamp": int(time.time()*1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "Email", "language": "English", "locale": "IN"}
}
r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=phish_msg)
check("Phishing turn 1 returns 200", r.status_code == 200)
resp = r.json()
check("Phishing scamDetected=true", resp.get("scamDetected") == True, str(resp.get("scamDetected")))

r = requests.get(f"{BASE_URL}/api/session/{phish_session}", headers=HEADERS)
intel = r.json().get("extractedIntelligence", {})
check("Phishing: extracted link", len(intel.get("phishingLinks",[])) > 0, str(intel.get("phishingLinks")))
check("Phishing: extracted email", len(intel.get("emailAddresses",[])) > 0, str(intel.get("emailAddresses")))

# ─── 7. Non-Scam Message ─────────────────────────────────
section("7. Non-Scam / Normal Message")

r = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json={
    "sessionId": "normal_msg_001",
    "message": {"sender": "scammer", "text": "Hello, how are you today?", "timestamp": int(time.time()*1000)},
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
})
check("Normal msg returns 200", r.status_code == 200)
check("Normal msg has reply", bool(r.json().get("reply")))

# ─── 8. API Docs ─────────────────────────────────────────
section("8. Auto-generated API Docs")

r = requests.get(f"{BASE_URL}/docs")
check("GET /docs returns 200", r.status_code == 200, "Swagger UI available")
r = requests.get(f"{BASE_URL}/redoc")
check("GET /redoc returns 200", r.status_code == 200, "ReDoc UI available")

# ─── Summary ─────────────────────────────────────────────
section("TEST SUMMARY")
passed = sum(1 for s,_,_ in results if s == PASS)
failed = sum(1 for s,_,_ in results if s == FAIL)
total = len(results)
print(f"\n  Passed : {passed}/{total}")
print(f"  Failed : {failed}/{total}")
print(f"\n  {'🎉 ALL TESTS PASSED!' if failed == 0 else '⚠️  Some tests failed — see above'}")

if failed > 0:
    print("\n  Failed tests:")
    for s, label, detail in results:
        if s == FAIL:
            print(f"    {FAIL} {label}: {detail}")

sys.exit(0 if failed == 0 else 1)
