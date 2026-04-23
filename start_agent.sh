#!/bin/bash
################################################################################
#                                                                              #
#  Agent-Larry v2.1 — QUICK START SCRIPT (Linux/macOS)                        #
#                                                                              #
#  Orchestrates full startup sequence:                                        #
#    1. Activate virtual environment                                          #
#    2. Run validation checks                                                 #
#    3. Initialize services                                                   #
#    4. Start the agent                                                       #
#                                                                              #
#  Usage:                                                                     #
#    bash start_agent.sh              # Full startup                          #
#    bash start_agent.sh --check      # Validation only                       #
#    bash start_agent.sh --quick      # Skip Ollama check                     #
#                                                                              #
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
LOG_DIR="${PROJECT_DIR}/logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="${LOG_DIR}/startup_${TIMESTAMP}.log"

# Configuration
OLLAMA_PORT=11434
OLLAMA_HOST="http://localhost:${OLLAMA_PORT}"
PYTHON_REQ="3.10"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level=$1
    shift
    local msg="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        success)
            echo -e "${GREEN}✓ ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
        error)
            echo -e "${RED}✗ ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
        warning)
            echo -e "${YELLOW}⚠ ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
        info)
            echo -e "${BLUE}ℹ ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
        step)
            echo -e "\n${CYAN}→ ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
        debug)
            echo -e "${CYAN}  ${msg}${NC}" | tee -a "$LOG_FILE"
            ;;
    esac
    
    echo "[${timestamp}] [${level}] ${msg}" >> "$LOG_FILE"
}

section_header() {
    local title=$1
    echo -e "\n${BLUE}${title:=═══════════════════════════════════════════════════════════════════}${NC}" | tee -a "$LOG_FILE"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# =============================================================================
# MAIN CHECKS
# =============================================================================

check_python() {
    section_header "Checking Python"
    
    if ! check_command python3; then
        log error "Python 3 not found. Install Python 3.10+"
        return 1
    fi
    
    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log success "Python $python_version found"
}

check_venv() {
    section_header "Checking Virtual Environment"
    
    if [ ! -d "$VENV_DIR" ]; then
        log warning "Virtual environment not found at $VENV_DIR"
        log info "Creating venv..."
        python3 -m venv "$VENV_DIR" || {
            log error "Failed to create venv"
            return 1
        }
        log success "Virtual environment created"
    else
        log success "Virtual environment found"
    fi
    
    # Activate venv
    source "$VENV_DIR/bin/activate" || {
        log error "Failed to activate venv"
        return 1
    }
    log success "Virtual environment activated"
}

check_directories() {
    section_header "Checking Directories"
    
    local dirs=(
        "data"
        "logs"
        "sandbox"
        "chroma_db"
        "context7_cache"
        "exports"
        "imports"
        "voice_cache"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "${PROJECT_DIR}/${dir}"
        log debug "Directory ready: $dir"
    done
    
    log success "All directories ready"
}

check_modules() {
    section_header "Checking Python Modules"
    
    log debug "Verifying core module files..."
    
    local modules=(
        "model_router.py"
        "file_browser.py"
        "agent_v2.py"
        "skill_manager.py"
        "mcp_client.py"
    )
    
    local missing=0
    for mod in "${modules[@]}"; do
        if [ -f "${PROJECT_DIR}/${mod}" ]; then
            log debug "✓ $mod"
        else
            log error "✗ $mod (missing)"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        log success "All core modules present"
        return 0
    else
        log error "Missing $missing core modules"
        return 1
    fi
}

check_ollama() {
    section_header "Checking Ollama Service"
    
    if ! check_command curl; then
        log warning "curl not available, skipping Ollama check"
        return 0
    fi
    
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        local model_count=$(curl -s "${OLLAMA_HOST}/api/tags" | grep -c '"name"' || echo "0")
        log success "Ollama running with $model_count models"
        return 0
    else
        log warning "Ollama not accessible at ${OLLAMA_HOST}"
        log info "Make sure Ollama is running: ollama serve"
        return 0  # Non-fatal
    fi
}

check_disk_space() {
    section_header "Checking Disk Space"
    
    local available=$(df "${PROJECT_DIR}" | awk 'NR==2 {print $4}')
    local available_gb=$((available / 1024 / 1024))
    
    if [ "$available_gb" -lt 5 ]; then
        log warning "Low disk space: ${available_gb}GB available (< 5GB)"
        return 0  # Non-fatal
    else
        log success "Disk space: ${available_gb}GB available"
        return 0
    fi
}

# =============================================================================
# IMPORT TESTS
# =============================================================================

test_imports() {
    section_header "Testing Python Imports"
    
    cd "$PROJECT_DIR"
    
    python3 << 'PYEOF'
import sys
import importlib

modules = [
    ("model_router", "Model routing"),
    ("file_browser", "File operations"),
    ("agent_v2", "Main agent"),
    ("skill_manager", "Skills"),
    ("mcp_client", "MCP toolkit"),
]

print(f"Testing {len(modules)} core imports...")

failed = []
for mod_name, desc in modules:
    try:
        importlib.import_module(mod_name)
        print(f"  ✓ {desc} ({mod_name})")
    except ImportError as e:
        print(f"  ✗ {desc} ({mod_name})")
        failed.append((mod_name, str(e)[:80]))

if failed:
    print(f"\n⚠ {len(failed)} import failures (may still work):")
    for mod, err in failed:
        print(f"    {mod}: {err}")
else:
    print(f"\n✓ All imports successful")

sys.exit(len(failed))
PYEOF
    
    if [ $? -eq 0 ]; then
        log success "All core imports successful"
        return 0
    else
        log warning "Some imports failed (may still work)"
        return 0
    fi
}

# =============================================================================
# STARTUP
# =============================================================================

show_banner() {
    cat << 'BANNER'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  AGENT-LARRY v2.1 — G-FORCE EDITION                       ║
║                                                                            ║
║        Your local AI agent with full skills and autonomous tools           ║
║                                                                            ║
║                  Everything runs locally. Nothing leaves here.            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

BANNER
}

startup_full() {
    show_banner
    
    mkdir -p "$LOG_DIR"
    
    log info "Startup log: $LOG_FILE"
    log step "Starting full initialization sequence..."
    
    check_python || { log error "Python check failed"; exit 1; }
    check_venv || { log error "Virtual environment check failed"; exit 1; }
    check_directories || { log error "Directory check failed"; exit 1; }
    check_modules || { log error "Modules check failed"; exit 1; }
    check_disk_space
    check_ollama
    test_imports || { log warning "Import test had issues"; }
    
    section_header "STARTUP COMPLETE"
    log success "All systems ready"
    log step "Starting Agent-Larry..."
    log info ""
    
    cd "$PROJECT_DIR"
    python3 START_AGENT.py
}

startup_check_only() {
    mkdir -p "$LOG_DIR"
    
    log info "Startup log: $LOG_FILE"
    log step "Running validation checks only..."
    
    check_python || { log error "Python check failed"; exit 1; }
    check_venv || { log error "Virtual environment check failed"; exit 1; }
    check_directories
    check_modules || { log warning "Some modules missing"; }
    check_disk_space
    check_ollama
    
    section_header "VALIDATION COMPLETE"
    log success "Setup is valid"
    log info "To start agent: bash start_agent.sh"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    case "${1:-}" in
        --check)
            startup_check_only
            ;;
        --quick)
            show_banner
            mkdir -p "$LOG_DIR"
            log info "Startup log: $LOG_FILE"
            log step "Quick startup (skipping Ollama check)..."
            check_python || { log error "Python check failed"; exit 1; }
            check_venv || { log error "Virtual environment check failed"; exit 1; }
            log success "Ready to start"
            log step "Starting Agent-Larry..."
            log info ""
            cd "$PROJECT_DIR"
            python3 START_AGENT.py --quick
            ;;
        *)
            startup_full
            ;;
    esac
}

main "$@"
