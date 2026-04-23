#!/bin/bash
# 🎯 UNIFIED SETUP GUIDE
# Complete setup for consolidated Agent-Larry workspace
# Integrates: current + compressedall + documentation

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1: ENVIRONMENT SETUP
# ════════════════════════════════════════════════════════════════════════════

print_phase() {
    echo ""
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_phase "PHASE 0: Pre-flight Checks"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

PY_VER=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PY_VER}${NC}"

# Check/activate venv
if [ ! -d ".venv" ] && [ ! -d "venv313" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv313" ]; then
    source venv313/bin/activate
fi

echo -e "${GREEN}✓ Virtual environment active${NC}"

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1: DEPENDENCIES
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 1: Install Dependencies"

if [ -f "requirements-linux.txt" ]; then
    echo "Installing extended dependencies from requirements-linux.txt..."
    pip install -r requirements-linux.txt -q
    echo -e "${GREEN}✓ Extended dependencies installed${NC}"
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓ Core dependencies installed${NC}"
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 2: CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 2: Configuration Setup"

# Check config files
if [ ! -f "larry_config.json" ]; then
    echo -e "${YELLOW}! larry_config.json not found${NC}"
else
    echo -e "${GREEN}✓ larry_config.json present${NC}"
fi

if [ ! -f "mcp.json" ]; then
    echo -e "${YELLOW}! mcp.json not found${NC}"
else
    echo -e "${GREEN}✓ mcp.json present${NC}"
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env template...${NC}"
    cat > .env << 'EOF'
# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# API Keys
BRAVE_API_KEY=
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=

# Ollama
OLLAMA_HOST=http://localhost:11434

# Disable telemetry
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY=False
POSTHOG_DISABLED=1
DO_NOT_TRACK=1
EOF
    echo -e "${YELLOW}Created .env template. Edit with your API keys.${NC}"
else
    echo -e "${GREEN}✓ .env present${NC}"
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 3: VALIDATE CORE MODULES
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 3: Validate Core Modules"

python3 << 'PYEOF'
import sys
modules_ok = []
modules_fail = []

test_modules = [
    ("agent_v2", "AgentLarry"),
    ("mcp_client", "MCPToolkit"),
    ("production_rag", "ProductionRAG"),
    ("web_tools", "WebScraper"),
]

for module_name, class_name in test_modules:
    try:
        mod = __import__(module_name)
        if hasattr(mod, class_name):
            modules_ok.append(f"✓ {module_name}")
        else:
            modules_ok.append(f"✓ {module_name} (partial)")
    except Exception as e:
        modules_fail.append(f"✗ {module_name}: {str(e)[:50]}")

for m in modules_ok:
    print(m)
for m in modules_fail:
    print(m)

sys.exit(1 if modules_fail else 0)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All core modules validated${NC}"
else
    echo -e "${YELLOW}! Some modules failed validation (check output above)${NC}"
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 4: OLLAMA CHECK
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 4: Ollama Status"

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "?")
        echo -e "${GREEN}✓ Ollama running ($MODELS models)${NC}"
    else
        echo -e "${YELLOW}! Ollama not running - start with: ollama serve${NC}"
    fi
else
    echo -e "${YELLOW}! Ollama not installed${NC}"
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 5: FEATURE CHECK
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 5: Feature Detection"

python3 << 'PYEOF'
import json
import os

features = {
    "MCP Support": False,
    "Production RAG": False,
    "Web Tools": False,
    "Telegram Bot": False,
    "Config Management": False,
}

try:
    from mcp_client import MCPToolkit
    features["MCP Support"] = True
except:
    pass

try:
    from production_rag import ProductionRAG
    features["Production RAG"] = True
except:
    pass

try:
    from web_tools import WebScraper
    features["Web Tools"] = True
except:
    pass

if os.path.exists("telegram_bot.py"):
    features["Telegram Bot"] = True

if os.path.exists("larry_config.json"):
    features["Config Management"] = True

for feature, available in features.items():
    icon = "✓" if available else "✗"
    print(f"{icon} {feature}")
PYEOF

# ════════════════════════════════════════════════════════════════════════════
# PHASE 6: QUICK START OPTIONS
# ════════════════════════════════════════════════════════════════════════════

print_phase "PHASE 6: Ready to Launch!"

echo -e "${BOLD}🚀 START AGENT:${NC}"
echo -e "  ${CYAN}python agent_v2.py${NC}"
echo ""

echo -e "${BOLD}📋 SAMPLE COMMANDS (in agent):${NC}"
echo -e "  Type: ${CYAN}list all current agent skills${NC}"
echo -e "  Type: ${CYAN}/skill config${NC}"
echo -e "  Type: ${CYAN}/skill model_profile${NC}"
echo -e "  Type: ${CYAN}/skill rag_settings${NC}"
echo -e "  Type: ${CYAN}/skill mcp_list${NC}"
echo ""

echo -e "${BOLD}🧠 DOCUMENTATION:${NC}"
echo -e "  Quick start:     ${CYAN}cat SKILLMANAGER_CHEATSHEET.md${NC}"
echo -e "  Full guide:      ${CYAN}cat SKILLMANAGER_GUIDE.md${NC}"
echo -e "  Feature map:     ${CYAN}cat CONTEXT_INVENTORY.md${NC}"
echo -e "  All docs:        ${CYAN}cat DOCUMENTATION_INDEX.md${NC}"
echo ""

echo -e "${BOLD}⚙️ SETUP OPTIONS:${NC}"
echo -e "  Run validation:  ${CYAN}python setup_larry.py --validate${NC}"
echo -e "  Full setup:      ${CYAN}python setup_larry.py${NC}"
echo ""

echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}✨ Setup Complete!${NC} Ready to launch Agent-Larry"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""
