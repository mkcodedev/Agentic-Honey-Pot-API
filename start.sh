#!/bin/bash
# Startup script for Linux/Mac

echo "========================================"
echo "  Agentic Honey-Pot API Server"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt
echo ""

# Run the server
echo "Starting FastAPI server..."
echo ""
python main.py
