#!/usr/bin/env bash
# QUICK START SCRIPT — Updated with Consolidated Approach
# Integrates compressedall context with current workspace

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         LARRY G-FORCE QUICK START (Consolidated)              ║"
    echo "║                   Ubuntu 24.04 • Python 3.13                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
}

print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# ════════════════════════════════════════════════════════════════════════════
# MAIN QUICK START
# ════════════════════════════════════════════════════════════════════════════

print_banner

# Check Python version
print_section "Python Environment"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "$(print_status "ok" "Using Python $PYTHON_VERSION")"

# Activate venv if exists
if [ -d ".venv" ]; then
    echo -e "$(print_status "ok" "Found .venv directory")"
    source .venv/bin/activate
elif [ -d "venv313" ]; then
    echo -e "$(print_status "ok" "Found venv313 directory")"
    source venv313/bin/activate
else
    echo -e "$(print_status "warn" "No virtual environment found")"
fi

# ════════════════════════════════════════════════════════════════════════════
# SHOW QUICK COMMANDS
# ════════════════════════════════════════════════════════════════════════════

print_section "Quick Commands"

echo -e "${BOLD}🚀 START AGENT:${NC}"
echo -e "  ${CYAN}python agent_v2.py${NC}"
echo -e "  Or with Ollama: ${CYAN}ollama serve &${NC} then ${CYAN}python agent_v2.py${NC}"

echo -e "\n${BOLD}🎨 MODELS & CONFIGURATION:${NC}"
echo -e "  Model settings: ${CYAN}cat larry_config.json${NC}"
echo -e "  Switch profile: ${CYAN}./agent_v2.py${NC} then type ${CYAN}/profile ACCURACY${NC}"
echo -e "  List models: ${CYAN}python -c \"from model_router import list_models; print(list_models())\"${NC}"

echo -e "\n${BOLD}🧠 RAG MEMORY:${NC}"
echo -e "  View RAG stats: ${CYAN}/rag${NC} (in agent)"
echo -e "  Index directory: ${CYAN}/index .${NC} (in agent)"
echo -e "  Search: ${CYAN}/search <query>${NC} (in agent)"

echo -e "\n${BOLD}📚 SETUP & VALIDATION:${NC}"
echo -e "  Full setup: ${CYAN}python setup_larry.py${NC}"
echo -e "  Validate: ${CYAN}python setup_larry.py --validate${NC}"
echo -e "  Check status: ${CYAN}python agent_v2.py${NC} then ${CYAN}/status${NC}"

echo -e "\n${BOLD}📱 TELEGRAM BOT:${NC}"
echo -e "  Start bot: ${CYAN}TELEGRAM_BOT_TOKEN=<token> python telegram_bot.py${NC}"
echo -e "  Set token in .env: ${CYAN}export TELEGRAM_BOT_TOKEN=your_token${NC}"

echo -e "\n${BOLD}🌐 WEB & RAG:${NC}"
echo -e "  Scrape URL: ${CYAN}/web <url>{{CN}}"
echo -e "  Search web: {{CYAN}}/search_web <query>${NC}"
echo -e "  YouTube: ${CYAN}}/youtube <url> summarize${NC}"

echo -e "\n${BOLD}🔧 DEVELOPMENT:{{NC}}"
echo -e "  Run tests: ${CYAN}python test_tools_comprehensive.py${NC}"
echo -e "  Check MCP: ${CYAN}python mcp_client.py${NC}"
echo -e "  View docs: ${CYAN}cat DOCUMENTATION_INDEX.md${NC}"

# ════════════════════════════════════════════════════════════════════════════
# DEPENDENCY CHECK
# ════════════════════════════════════════════════════════════════════════════

print_section "Dependency Check"

# Check for key packages
PACKAGES=("requests" "ollama" "chromadb" "sentence_transformers" "fastapi")

for pkg in "${PACKAGES[@]}"; do
    python -c "import $pkg" 2>/dev/null && \
        echo -e "$(print_status "ok" "$pkg")" || \
        echo -e "$(print_status "warn" "$pkg (not installed)")"
done

# ════════════════════════════════════════════════════════════════════════════
# QUICK STATUS
# ════════════════════════════════════════════════════════════════════════════

print_section "Component Status"

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "$(print_status "ok" "Ollama: installed")"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        MODELS=$(curl -s http://localhost:11434/api/tags | python -c "import sys, json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "?")
        echo -e "$(print_status "ok" "Ollama: running ($MODELS models)")"
    else
        echo -e "$(print_status "warn" "Ollama: not running (start with: ollama serve)")"
    fi
else
    echo -e "$(print_status "warn" "Ollama: not installed")"
fi

# Check config files
[ -f "larry_config.json" ] && echo -e "$(print_status "ok" "larry_config.json")" || echo -e "$(print_status "warn" "larry_config.json (not found)")"
[ -f "mcp.json" ] && echo -e "$(print_status "ok" "mcp.json")" || echo -e "$(print_status "warn" "mcp.json (not found)")"
[ -f ".env" ] && echo -e "$(print_status "ok" ".env")" || echo -e "$(print_status "warn" ".env (create with: cp .env.example .env)")"

# ════════════════════════════════════════════════════════════════════════════
# NEXT STEPS
# ════════════════════════════════════════════════════════════════════════════

print_section "Next Steps"

echo -e "${BOLD}1. Prepare Ollama${NC}"
echo -e "   ${CYAN}ollama serve &${NC}"
echo -e "   ${CYAN}ollama pull dolphin-mixtral:8x7b${NC}"

echo -e "\n${BOLD}2. Start Agent${NC}"
echo -e "   ${CYAN}python agent_v2.py${NC}"

echo -e "\n${BOLD}3. Try Commands{{NC}}"
echo -e "   Type: ${CYAN}/help{{NC}}"
echo -e "   Or: {{CYAN}}/status${NC}"
echo -e "   Or: {{CYAN}}/models${NC}"

echo -e "\n${BOLD}4. Explore Features${NC}"
echo -e "   RAG: {{CYAN}}/rag{{NC}}"
echo -e "   Index: {{CYAN}}/index .${NC}"
echo -e "   Search: {{CYAN}}/search llama${NC}"

# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTATION
# ════════════════════════════════════════════════════════════════════════════

print_section "Documentation"

DOCS=(
    "SKILLMANAGER_CHEATSHEET.md:5 min quick start"
    "SKILLMANAGER_GUIDE.md:Full production guide"
    "README.md:Architecture & features"
    "DOCUMENTATION_INDEX.md:Navigation guide"
    "CONTEXT_INVENTORY.md:Unused features & configs"
)

for doc in "${DOCS[@]}"; do
    IFS=':' read -r file desc <<< "$doc"
    [ -f "$file" ] && echo -e "$(print_status "ok" "$file - $desc")" || echo -e "$(print_status "warn" "$file not found")"
done

# ════════════════════════════════════════════════════════════════════════════
# CONSOLIDATED INFO
# ════════════════════════════════════════════════════════════════════════════

print_section "Consolidated Configuration"

echo -e "${BOLD}This workspace includes:{{NC}}"
echo -e "✓ Current workspace (GPU-optimized, portable)"
echo -e "✓ Compressedall archive context (model profiles, MCP setup)"
echo -e "✓ setup_larry.py (environment validation and setup)"
echo -e "✓ requirements-linux.txt (120+ dependencies documented)"
echo -e "✓ telegram_botOG.py (archived reference)"

echo -e "\n${BOLD}New integrated features:${NC}"
echo -e "✓ larry_config.json with model profiles (SPEED/BALANCED/ACCURACY)"
echo -e "✓ MCP server catalog (8+ native servers)"
echo -e "✓ ProfileManager for hardware utilization"
echo -e "✓ Production RAG with reranking"
echo -e "✓ Unified context management"
echo -e "✓ Network security commands (ports, threats, devices)"

# ════════════════════════════════════════════════════════════════════════════
# DONE
# ════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}✨ Setup complete! Ready to launch!${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "First time? Read: ${CYAN}cat SKILLMANAGER_CHEATSHEET.md${NC}"
echo -e "Ready to start? Run: {{CYAN}python agent_v2.py${NC}}"
echo ""
