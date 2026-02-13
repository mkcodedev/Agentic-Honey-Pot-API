# Agentic Honey-Pot (Scam Detection & Intelligence Extraction)

This project is an AI-powered honeypot system designed to detect scam messages, engage scammers autonomously, and extract actionable intelligence.

## Quick Start

1.  **Start Everything**: Double-click `run_all.bat`.
    - This will open 3 windows: 
        1. **Backend**: FastAPI server running on `http://localhost:8000`
        2. **Frontend**: Streamlit UI running on your browser (if it works)
        3. **Terminal**: A backup terminal-based chat client (use this if Streamlit fails)

2.  **Access the API**:
    - Docs: `http://localhost:8000/docs`
    - Endpoint: `POST /api/honeypot`
    - Key: `sk_honeypot_live_a8f92c3e4b5d6789xyz` (Configured in `.env`)

## Features

-   **Scam Detection**: Uses keywords and patterns (bank accounts, urgency) to detect scams.
-   **Autonomous Agent**: Engages scammers using confused/elderly persona to draw out details.
-   **Intelligence Extraction**: Automatically extracts Upl IDs, phone numbers, and bank accounts.
-   **Callback Reporting**: Once sufficient engagement (8+ messages) and scam detection occurs, sends a report to the hackathon evaluation endpoint.

## Troubleshooting

-   **Frontend crashes**: If `app.py` fails with `TypeError` (common on Python 3.14+), use the "Agentic Honey-Pot TERMINAL" window to chat with the bot instead.
-   **Backend logs**: Check the backend window for "Callback sent successfully" messages.

## Configuration

-   Edit `.env` to change API keys or backend URL locally.
