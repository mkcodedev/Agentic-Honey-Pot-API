import streamlit as st
import requests
import time
import uuid
import os
import pandas as pd

st.set_page_config(page_title="Agentic Honey-Pot", layout="wide", page_icon="🔒")

# --- Custom CSS ---
st.markdown("""
<style>
    /* Base */
    body { font-family: 'Inter', sans-serif; }
    .main { background-color: #0d1117; color: #c9d1d9; }
    
    /* Layout */
    .stApp > header { display: none; }
    .st-emotion-cache-1jicfl2 { gap: 2rem; } /* main columns gap */

    /* Sidebar */
    .st-emotion-cache-16txtl3 { padding: 1.5rem; background-color: #010409; border-right: 1px solid #30363d; }
    .st-emotion-cache-16txtl3 h1 { font-size: 1.5rem; font-weight: 600; color: #f0f6fc; }
    .st-emotion-cache-16txtl3 .st-emotion-cache-1v0mbdj { font-size: 0.8rem; color: #8b949e; } /* version */
    .st-emotion-cache-16txtl3 h2 { font-size: 0.75rem; font-weight: 600; color: #8b949e; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 1.5rem; margin-bottom: 0.5rem; }
    .st-emotion-cache-16txtl3 .st-emotion-cache-qbe2p { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 0.5rem; } /* session info box */
    .st-emotion-cache-16txtl3 .st-emotion-cache-qbe2p .st-emotion-cache-1r4qj8v { font-size: 0.9rem; }
    .st-emotion-cache-16txtl3 .st-emotion-cache-qbe2p .st-emotion-cache-1r4qj8v:first-child { color: #8b949e; }
    .st-emotion-cache-16txtl3 .st-emotion-cache-qbe2p .st-emotion-cache-1r4qj8v:last-child { color: #c9d1d9; font-weight: 600; }
    .st-emotion-cache-16txtl3 .st-emotion-cache-ue6h4q { width: 100%; } /* reset button */
    .st-emotion-cache-16txtl3 .st-emotion-cache-1kyxreq { border-radius: 6px; } /* input widgets */
    .st-emotion-cache-16txtl3 .st-emotion-cache-1kyxreq div[data-baseweb="base-input"] { background-color: #010409; }

    /* Main Chat Area */
    .st-emotion-cache-1jicfl2 > div:first-child { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.5rem; }
    .st-emotion-cache-1jicfl2 h3 { font-size: 1.1rem; font-weight: 600; color: #f0f6fc; }
    .st-emotion-cache-1jicfl2 .st-emotion-cache-1629p8f { font-size: 0.8rem; color: #8b949e; } /* e2ee locked */
    .st-emotion-cache-1jicfl2 .st-chat-input { background-color: #0d1117; }
    .st-emotion-cache-1jicfl2 .st-emotion-cache-13p4w2i { border-top: 1px solid #30363d; padding-top: 1rem; } /* chat input container */
    .st-emotion-cache-1jicfl2 .st-emotion-cache-1c7y2kd { font-size: 0.8rem; color: #8b949e; text-align: center; padding-top: 0.5rem; } /* footer */
    .st-emotion-cache-1jicfl2 .st-emotion-cache-4oygw6 { height: 500px; } /* chat container */
    .st-emotion-cache-4oygw6 .st-emotion-cache-1c7y2kd { text-align: center; padding-top: 10rem; } /* waiting message */
    .st-emotion-cache-4oygw6 .st-emotion-cache-1c7y2kd p { font-size: 1rem; }
    .st-emotion-cache-4oygw6 .st-emotion-cache-1c7y2kd .st-emotion-cache-1v0mbdj { font-size: 2rem; opacity: 0.3; }
    .st-emotion-cache-1c7y2kd { color: #8b949e; }
    
    /* Right Sidebar */
    .st-emotion-cache-1jicfl2 > div:last-child { display: flex; flex-direction: column; gap: 1.5rem; }
    .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; }
    .card h4 { font-size: 0.9rem; font-weight: 600; color: #f0f6fc; margin-bottom: 0.5rem; }
    .card p { font-size: 0.9rem; color: #8b949e; }
    .pipeline-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .pipeline-grid h5 { font-size: 0.7rem; font-weight: 600; color: #8b949e; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem; }
    .pipeline-grid ul { list-style-type: none; padding-left: 0; margin: 0; }
    .pipeline-grid li { font-size: 0.9rem; color: #c9d1d9; margin-bottom: 0.25rem; }
    .awaiting-data { text-align: center; padding: 2rem 1rem; }
    .awaiting-data .icon { font-size: 2.5rem; opacity: 0.5; }
    .awaiting-data p { font-size: 1rem; color: #8b949e; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if "messages" not in st.session_state: st.session_state.messages = []
if "session_id" not in st.session_state: st.session_state.session_id = f"session-{uuid.uuid4().hex[:12]}"
if "intel" not in st.session_state: st.session_state.intel = {"bankAccounts":[], "upiIds":[], "phishingLinks":[], "phoneNumbers":[], "suspiciousKeywords":[]}
if "scam_detected" not in st.session_state: st.session_state.scam_detected = False

# --- Backend Config ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "PROD_SECRET_123")

# --- UI LAYOUT ---

# --- 1. SIDEBAR ---
with st.sidebar:
    st.title("Agentic Honey-Pot")
    st.caption("AGENTIC HONEY-POT V1.0.4")
    
    st.header("Session Info")
    with st.container():
        st.info(f"Environment: Local (Production Mode)")
        st.info(f"Session ID: {st.session_state.session_id}")
        st.info(f"Messages: {len(st.session_state.messages)}")
    
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.intel = {"bankAccounts":[], "upiIds":[], "phishingLinks":[], "phoneNumbers":[], "suspiciousKeywords":[]}
        st.session_state.scam_detected = False
        st.session_state.session_id = f"session-{uuid.uuid4().hex[:12]}"
        st.rerun()

    st.header("Channel Settings")
    channel = st.selectbox("Channel", ["WhatsApp", "SMS", "Email", "Telegram"])
    language = st.text_input("Language", "English")
    locale = st.text_input("Locale", "IN")

# --- 2. MAIN & RIGHT COLUMNS ---
col_main, col_right = st.columns([2, 1.2])

# --- 3. MAIN CHAT INTERFACE ---
with col_main:
    st.subheader("🔒 Secure Chat Terminal")
    
    # Chat Window
    chat_container = st.container(height=500, border=False)
    with chat_container:
        if not st.session_state.messages:
            st.markdown('<div style="text-align: center; padding-top: 10rem; opacity: 0.5;">'
                        '<h2>...</h2>'
                        '<p>Waiting for incoming scammer connection...</p>'
                        '</div>', unsafe_allow_html=True)
        else:
            for message in st.session_state.messages:
                with st.chat_message("user" if message["sender"] == "scammer" else "assistant"):
                    st.write(message["text"])

    # Chat Input
    if prompt := st.chat_input("Simulate scammer message here..."):
        st.session_state.messages.append({"sender": "scammer", "text": prompt, "timestamp": int(time.time() * 1000)})
        
        with st.spinner("Agent is thinking..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/honeypot",
                    json={
                        "sessionId": st.session_state.session_id,
                        "message": st.session_state.messages[-1],
                        "conversationHistory": st.session_state.messages[:-1],
                        "metadata": {"channel": channel, "language": language, "locale": locale}
                    },
                    headers={"x-api-key": API_KEY},
                    timeout=30
                )
                
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.messages.append({"sender": "assistant", "text": data["reply"], "timestamp": int(time.time() * 1000)})
                    st.session_state.scam_detected = data["scamDetected"]
                    
                    # Update intelligence
                    for key in st.session_state.intel:
                        if key in data.get("intelligence", {}):
                            new_intel = data["intelligence"][key]
                            st.session_state.intel[key] = list(set(st.session_state.intel[key] + new_intel))
                    st.rerun()
                else:
                    st.error(f"Backend Error: {res.status_code} - {res.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Backend unreachable: {e}")

    st.caption("Honeypot mode active • AI Persona: Mr. Gupta • Indian Locale")


# --- 4. RIGHT INTELLIGENCE PANEL ---
with col_right:
    # Status Card
    with st.container(border=True):
        st.markdown("#### ⓘ Status")
        if any(st.session_state.intel.values()):
            st.success("Intelligence has been extracted.")
        else:
            st.info("No intelligence extracted yet. Use persona prompts to draw out details.")

    # Data Extraction Pipeline Card
    with st.container(border=True):
        st.markdown("#### 📊 Data Extraction Pipeline")
        st.caption("AI system actively monitoring and extracting:")
        
        intel_categories = {
            "FINANCIAL DATA": ("bankAccounts", "upiIds"),
            "DIGITAL FOOTPRINT": ("phishingLinks",),
            "CONTACT INFO": ("phoneNumbers",),
            "BEHAVIORAL PATTERNS": ("suspiciousKeywords",)
        }
        
        cols = st.columns(2)
        col_idx = 0
        for category, keys in intel_categories.items():
            with cols[col_idx]:
                st.markdown(f"**{category}**")
                for key in keys:
                    title = key.replace('_', ' ').title()
                    items = st.session_state.intel.get(key, [])
                    st.text(f"• {title} ({len(items)})")
                    if items:
                        for item in items:
                            st.code(item, language=None)
            col_idx = (col_idx + 1) % 2

    # Awaiting Data Card
    if not any(st.session_state.intel.values()):
        with st.container(border=True):
            st.markdown('<div class="awaiting-data"><div class="icon">⏳</div><p>Awaiting Data</p></div>', unsafe_allow_html=True)
