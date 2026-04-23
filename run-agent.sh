#!/bin/bash
# =============================================
# Agent Larry G-FORCE — FULL AUTO SETUP
# MCP Tools + Skills + qwen3-coder:30b
# =============================================

cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "🛠️  Creating virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating venv..."
source venv/bin/activate

echo "📦 Installing ALL required dependencies..."
pip install --upgrade pip
pip install \
    requests rich pandas pyyaml tiktoken apscheduler \
    beautifulsoup4 html2text python-dotenv \
    playwright faster-whisper TTS \
    chromadb sentence-transformers torch torchvision torchaudio \
    pillow pypdf toml PyMuPDF \
    python-dotenv pyreadline3

# Install Playwright browsers (needed for MCP Playwright server)
playwright install --with-deps chromium

echo "🦙 Pulling qwen3-coder:30b (this may take a few minutes)..."
ollama pull qwen3-coder:30b

echo "🚀 Starting LARRY G-FORCE with full MCP + Skills support..."
echo "   Preferred model: qwen3-coder:30b"
python agent_v2.py
