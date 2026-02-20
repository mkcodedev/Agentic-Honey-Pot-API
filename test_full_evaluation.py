"""
Full end-to-end evaluation test that mimics the hackathon evaluator.
Runs multi-turn conversations for all 3 scenarios and prints a score report.

Usage: python test_full_evaluation.py
"""

import time
import json
import requests
from typing import List, Dict, Any, Optional

BASE_URL   = "http://localhost:8000"
API_KEY    = "sk_honeypot_live_a8f92c3e4b5d6789xyz"
HEADERS    = {"Content-Type": "application/json", "x-api-key": API_KEY}


# ─── Scenario definitions ─────────────────────────────────────────────────────

SCENARIOS = [
    {
        "name": "Bank Fraud Detection",
        "type": "bank_fraud",
        "weight": 35,
        "session_id": "test-bank-001",
        "turns": [
            "URGENT: Your SBI account has been compromised. Call us immediately or your account will be blocked in 2 hours!",
            "I'm calling from SBI Fraud Department. My employee ID is SBI-12345. What is your account number so I can verify?",
            "Yes sir, I found the issue. Your account number 1234567890123456 has been flagged. You need to share the OTP sent to your phone RIGHT NOW.",
            "For security, transfer Rs 5000 to this verified SBI account: 9876543210987654. This is just a verification hold.",
            "Sir please hurry! You can contact me back at +91-9876543210 if you need. But we must complete this now.",
            "Also, please send money via UPI to scammer.fraud@fakebank for the verification fee. Just Rs 999, it will be refunded.",
            "Sir, this is your last chance. The RBI has issued order RBI-002345 against your account. Act NOW.",
            "Fine. Here is my supervisor's number too: 9123456789. He will confirm the freeze if you call. Please cooperate.",
        ],
        # All fake intelligence planted in the conversation
        "fake_data": {
            "phoneNumbers": ["+919876543210", "9123456789"],
            "bankAccounts": ["1234567890123456", "9876543210987654"],
            "upiIds": ["scammer.fraud@fakebank"],
            "caseIds": ["SBI-12345", "RBI-002345"],
        },
    },
    {
        "name": "UPI Fraud Multi-turn",
        "type": "upi_fraud",
        "weight": 35,
        "session_id": "test-upi-001",
        "turns": [
            "Congratulations! You've won Rs 50,000 cashback from PhonePe Lucky Draw! You are selected customer number 1047.",
            "To receive your prize, just send a small verification amount of Rs 99 to cashback.scam@fakeupi",
            "Our support agent is reachable at +91-8765432109. Please call to process your reward.",
            "For quick processing send to backup UPI also: winner.prize@upi — this ensures same-day credit.",
            "Your order ID is ORD-789456 which is tied to this lucky draw. Provide your UPI PIN to link your reward.",
            "We also need your registered email to send the certificate: claim.prize@winner-lottery.com — this is our official domain.",
            "Time is running out! Your winning entry expires in 30 mins. Your case reference is CASE-654321.",
            "Our official website: http://phonep3-cashback.lucky-prize.com/claim?user=1047 — just login and claim!",
        ],
        "fake_data": {
            "upiIds": ["cashback.scam@fakeupi", "winner.prize@upi"],
            "phoneNumbers": ["+918765432109"],
            "emailAddresses": ["claim.prize@winner-lottery.com"],
            "orderNumbers": ["ORD-789456"],
            "caseIds": ["CASE-654321"],
            "phishingLinks": ["http://phonep3-cashback.lucky-prize.com/claim?user=1047"],
        },
    },
    {
        "name": "Phishing Link Detection",
        "type": "phishing",
        "weight": 30,
        "session_id": "test-phishing-001",
        "turns": [
            "SPECIAL OFFER: Get iPhone 15 Pro at just Rs.999! Limited stock. Click now: http://amaz0n-deals.fake-site.com/claim?id=12345",
            "You can also email us for assistance: offers@fake-amazon-deals.com or support@amaz0n-help.net",
            "Call our customer care: +91-9988776655 to confirm your order. Use order ID ORD-IPHONE-001 when calling.",
            "For extra discount use policy code POL-GOLD-999 at checkout on our site.",
            "If the first link doesn't work try: http://bit.ly/fakeAmazon123 — same offer!",
            "Your personal shopper helpline: 8877665544. Please call between 9am-9pm.",
            "To track your parcel visit http://tracking.amaz0n-fake.in/status?order=12345 and enter your details.",
            "Final reminder — offer ends today! Contact: scam.seller@gmail.com or visit our page.",
        ],
        "fake_data": {
            "phishingLinks": [
                "http://amaz0n-deals.fake-site.com/claim?id=12345",
                "http://bit.ly/fakeAmazon123",
                "http://tracking.amaz0n-fake.in/status?order=12345",
            ],
            "emailAddresses": ["offers@fake-amazon-deals.com", "support@amaz0n-help.net", "scam.seller@gmail.com"],
            "phoneNumbers": ["+919988776655", "8877665544"],
            "orderNumbers": ["ORD-IPHONE-001"],
            "policyNumbers": ["POL-GOLD-999"],
        },
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def post_turn(session_id: str, text: str, history: List[Dict]) -> Dict:
    """Send one turn to /api/honeypot and return response dict"""
    body = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text":   text,
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": history,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
    }
    r = requests.post(f"{BASE_URL}/api/honeypot", json=body, headers=HEADERS, timeout=30)
    return r.json()


def get_session(session_id: str) -> Dict:
    r = requests.get(f"{BASE_URL}/api/session/{session_id}", headers=HEADERS, timeout=10)
    return r.json()


def get_final_output(session_id: str) -> Dict:
    r = requests.post(f"{BASE_URL}/api/final", params={"session_id": session_id},
                      headers=HEADERS, timeout=15)
    return r.json()


# ─── Scoring replication ──────────────────────────────────────────────────────

def score_scenario(session_data: Dict, final_output: Dict, fake_data: Dict) -> Dict:
    """Replicate the hackathon scoring rubric for one scenario (100 pts)"""
    scores = {}
    details = {}

    # ── 1. Scam Detection (20 pts) ──────────────────────────────────────────
    scam_detected = (final_output.get("finalOutput") or {}).get("scamDetected", False)
    scores["detection"] = 20 if scam_detected else 0
    details["detection"] = f"scamDetected={scam_detected}"

    # ── 2. Extracted Intelligence (30 pts) ─────────────────────────────────
    total_fake = sum(len(v) for v in fake_data.values())
    pts_per_item = 30 / total_fake if total_fake else 0
    intel = (final_output.get("finalOutput") or {}).get("extractedIntelligence", {})

    extracted_count = 0
    intel_details = {}
    for field, planted in fake_data.items():
        extracted = intel.get(field, [])
        matched = []
        for p in planted:
            # Normalize both sides
            p_norm = p.lower().replace("-", "").replace("+91", "").strip()
            for e in extracted:
                e_norm = e.lower().replace("-", "").replace("+91", "").strip()
                if p_norm in e_norm or e_norm in p_norm:
                    matched.append(p)
                    break
        intel_details[field] = f"{len(matched)}/{len(planted)} matched: {matched}"
        extracted_count += len(matched)

    intel_score = round(min(30, extracted_count * pts_per_item), 1)
    scores["extraction"] = intel_score
    details["extraction"] = intel_details

    # ── 3. Conversation Quality (30 pts) ───────────────────────────────────
    turns      = session_data.get("conversationLength", 0)
    questions  = session_data.get("questionsAsked", 0)
    red_flags  = len(session_data.get("redFlagsFound", []))
    elicit     = session_data.get("elicitationAttempts", 0)

    # Turn count (8 pts)
    turn_score = 8 if turns >= 8 else (6 if turns >= 6 else (3 if turns >= 4 else 0))
    # Questions asked (4 pts)
    q_score = 4 if questions >= 5 else (2 if questions >= 3 else (1 if questions >= 1 else 0))
    # Relevant questions (3 pts) — approximated from questionsAsked
    rq_score = 3 if questions >= 3 else (2 if questions >= 2 else (1 if questions >= 1 else 0))
    # Red flags (8 pts)
    rf_score = 8 if red_flags >= 5 else (5 if red_flags >= 3 else (2 if red_flags >= 1 else 0))
    # Elicitation (7 pts, 1.5 pts each, max 7)
    el_score = min(7, round(elicit * 1.5, 1))

    conv_score = turn_score + q_score + rq_score + rf_score + el_score
    scores["conversation"] = conv_score
    details["conversation"] = {
        "turns": f"{turns} → {turn_score}/8",
        "questions_asked": f"{questions} → {q_score}/4",
        "relevant_questions": f"{questions} → {rq_score}/3",
        "red_flags": f"{red_flags} → {rf_score}/8",
        "elicitation": f"{elicit} → {el_score}/7",
    }

    # ── 4. Engagement Quality (10 pts) ─────────────────────────────────────
    duration = session_data.get("engagementDurationSeconds", 0)
    msgs     = session_data.get("totalMessagesExchanged", 0)

    eng = 0
    if duration > 0:   eng += 1
    if duration > 60:  eng += 2
    if duration > 180: eng += 1
    if msgs > 0:       eng += 2
    if msgs >= 5:      eng += 3
    if msgs >= 10:     eng += 1

    scores["engagement"] = min(10, eng)
    details["engagement"] = f"duration={duration}s, msgs={msgs}"

    # ── 5. Response Structure (10 pts) ──────────────────────────────────────
    fo = final_output.get("finalOutput") or {}
    struct = 0
    missing = []
    if fo.get("sessionId"):     struct += 2
    else:                        missing.append("sessionId")
    if "scamDetected" in fo:    struct += 2
    else:                        missing.append("scamDetected")
    if fo.get("extractedIntelligence"): struct += 2
    else:                        missing.append("extractedIntelligence")
    metrics_present = fo.get("totalMessagesExchanged") and fo.get("engagementDurationSeconds")
    if metrics_present: struct += 1
    if fo.get("agentNotes"):    struct += 1
    if fo.get("scamType"):      struct += 1
    if fo.get("confidenceLevel"): struct += 1
    struct -= len(missing)  # -1 per missing required

    scores["structure"] = max(0, struct)
    details["structure"] = f"present fields OK, missing={missing}"

    scores["total"] = sum(scores.values())
    return {"scores": scores, "details": details}


# ─── Main test runner ─────────────────────────────────────────────────────────

def run_scenario(scenario: Dict):
    session_id  = scenario["session_id"]
    turns_text  = scenario["turns"]
    fake_data   = scenario["fake_data"]

    print(f"\n{'='*70}")
    print(f"  SCENARIO: {scenario['name']}  (weight {scenario['weight']}%)")
    print(f"{'='*70}")

    history: List[Dict] = []
    reply_count = 0

    for i, turn_text in enumerate(turns_text):
        print(f"\n  Turn {i+1} — Scammer: {turn_text[:80]}...")
        resp = post_turn(session_id, turn_text, history)
        reply = resp.get("reply", resp.get("message", ""))
        print(f"  Agent: {reply[:120]}...")

        # Update history
        history.append({"sender": "scammer", "text": turn_text, "timestamp": int(time.time()*1000)})
        history.append({"sender": "user",    "text": reply,      "timestamp": int(time.time()*1000)})
        reply_count += 1
        time.sleep(0.5)  # small delay to accumulate engagement time

    print(f"\n  → Sending /api/final...")
    final = get_final_output(session_id)
    session = get_session(session_id)

    print(f"\n  ── Final Output Preview ──────────────────────────")
    fo = final.get("finalOutput") or {}
    print(f"  scamDetected:         {fo.get('scamDetected')}")
    print(f"  scamType:             {fo.get('scamType')}")
    print(f"  confidenceLevel:      {fo.get('confidenceLevel')}")
    print(f"  totalMessages:        {fo.get('totalMessagesExchanged')}")
    print(f"  engagementSeconds:    {fo.get('engagementDurationSeconds')}")
    print(f"  agentNotes:           {str(fo.get('agentNotes',''))[:100]}")
    ei = fo.get("extractedIntelligence") or {}
    print(f"  ── Extracted Intelligence ─────────────────────────")
    for k, v in ei.items():
        if v:
            print(f"    {k}: {v}")
    print(f"  ── Session Tracking ───────────────────────────────")
    print(f"  questionsAsked:       {session.get('questionsAsked')}")
    print(f"  elicitationAttempts:  {session.get('elicitationAttempts')}")
    print(f"  redFlagsFound:        {session.get('redFlagsFound')}")
    print(f"  callbackSent:         {session.get('callbackSent')}")

    # Score
    result = score_scenario(session, final, fake_data)
    scores = result["scores"]
    details = result["details"]

    print(f"\n  ── Score Breakdown ────────────────────────────────")
    print(f"  Detection:      {scores['detection']:5.1f} / 20  {details['detection']}")
    extr_d = details['extraction']
    print(f"  Extraction:     {scores['extraction']:5.1f} / 30")
    for f, d in extr_d.items():
        print(f"    {f}: {d}")
    conv_d = details['conversation']
    print(f"  Conversation:   {scores['conversation']:5.1f} / 30")
    for k, v in conv_d.items():
        print(f"    {k}: {v}")
    print(f"  Engagement:     {scores['engagement']:5.1f} / 10  {details['engagement']}")
    print(f"  Structure:      {scores['structure']:5.1f} / 10  {details['structure']}")
    print(f"  ──────────────────────────────────────────────────")
    print(f"  TOTAL:          {scores['total']:5.1f} / 100")

    return {"name": scenario["name"], "weight": scenario["weight"], "score": scores["total"], "scores": scores}


def main():
    print("\n🍯  AGENTIC HONEY POT — Full Evaluation Test")
    print(f"    Server: {BASE_URL}")
    print(f"    API Key: {API_KEY[:20]}...")

    # Health check
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"    Health: {r.json().get('status')}")
    except Exception as e:
        print(f"   ❌ Server not reachable: {e}")
        return

    scenario_results = []
    for scenario in SCENARIOS:
        result = run_scenario(scenario)
        scenario_results.append(result)

    # Final weighted score
    print(f"\n{'='*70}")
    print("  FINAL WEIGHTED SCORE CALCULATION")
    print(f"{'='*70}")
    weighted_total = 0
    for r in scenario_results:
        contribution = r["score"] * r["weight"] / 100
        weighted_total += contribution
        print(f"  {r['name']:<35} {r['score']:5.1f}/100  × {r['weight']}% = {contribution:5.2f}")

    scenario_portion = weighted_total * 0.9
    print(f"\n  Weighted Scenario Score:     {weighted_total:.2f}")
    print(f"  Scenario Portion (×0.9):     {scenario_portion:.2f}")
    print(f"  Code Quality (est 8/10):     8.00")
    print(f"  ESTIMATED FINAL SCORE:       {scenario_portion + 8:.2f} / 100")

    # Pain points
    print(f"\n{'='*70}")
    print("  ISSUES TO FIX (score < 80 in any component)")
    print(f"{'='*70}")
    any_issue = False
    for r in scenario_results:
        s = r["scores"]
        issues = []
        if s["detection"] < 20:  issues.append(f"Detection {s['detection']}/20")
        if s["extraction"] < 24: issues.append(f"Extraction {s['extraction']}/30 (<80%)")
        if s["conversation"] < 24: issues.append(f"Conversation {s['conversation']}/30 (<80%)")
        if s["engagement"] < 8:  issues.append(f"Engagement {s['engagement']}/10 (<80%)")
        if s["structure"] < 8:   issues.append(f"Structure {s['structure']}/10 (<80%)")
        if issues:
            print(f"  {r['name']}: {', '.join(issues)}")
            any_issue = True
    if not any_issue:
        print("  ✅ All components ≥80% — looking good!")


if __name__ == "__main__":
    main()
