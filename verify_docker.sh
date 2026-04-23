#!/usr/bin/env bash
# ============================================================================
# verify_docker.sh — Docker deployment verification for Agent Larry
# ============================================================================
# Run on any machine (Ubuntu, macOS, Windows WSL) to confirm Docker setup.
#
# Usage:
#   chmod +x verify_docker.sh
#   ./verify_docker.sh
# ============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
PASS=0
FAIL=0
WARN=0

pass()  { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; WARN=$((WARN+1)); }

echo "============================================"
echo "  Agent Larry — Docker Verification"
echo "============================================"
echo ""

# ── 1. Docker Engine ────────────────────────────────────────────────────────
echo "--- Docker Engine ---"
if command -v docker >/dev/null 2>&1; then
    DVER=$(docker --version 2>&1)
    pass "Docker installed: $DVER"
else
    fail "Docker not found. Install: https://docs.docker.com/engine/install/"
    echo "Cannot continue without Docker."
    exit 1
fi

if docker info >/dev/null 2>&1; then
    pass "Docker daemon is running"
else
    fail "Docker daemon not running. Start with: sudo systemctl start docker"
    exit 1
fi

# ── 2. Docker Compose ──────────────────────────────────────────────────────
echo ""
echo "--- Docker Compose ---"
if docker compose version >/dev/null 2>&1; then
    CVER=$(docker compose version --short 2>&1)
    pass "Docker Compose v$CVER"
else
    fail "Docker Compose plugin not found. Install: sudo apt install docker-compose-plugin"
fi

# ── 3. Project Files ───────────────────────────────────────────────────────
echo ""
echo "--- Project Files ---"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

for f in Dockerfile docker-compose.yml .env .env.secret.example requirements.txt larry_config.json mcp.json larry_paths.py agent_v2.py; do
    if [ -f "$f" ]; then
        pass "$f exists"
    else
        fail "$f missing"
    fi
done

if [ -f ".env.secret" ]; then
    pass ".env.secret exists (secrets configured)"
else
    warn ".env.secret not found — copy from .env.secret.example"
fi

# ── 4. Docker Compose Config Validation ────────────────────────────────────
echo ""
echo "--- Compose Config ---"
if docker compose config --quiet 2>/dev/null; then
    pass "docker-compose.yml is valid"
else
    fail "docker-compose.yml has errors — run: docker compose config"
fi

# ── 5. Docker Image ───────────────────────────────────────────────────────
echo ""
echo "--- Docker Image ---"
if docker image inspect larry-agent:latest >/dev/null 2>&1; then
    SIZE=$(docker image inspect larry-agent:latest --format '{{.Size}}' | awk '{printf "%.0f MB", $1/1048576}')
    pass "larry-agent:latest exists ($SIZE)"
else
    warn "larry-agent:latest not built yet — run: docker build -t larry-agent:latest ."
fi

# ── 6. GPU (Linux with NVIDIA only) ───────────────────────────────────────
echo ""
echo "--- GPU ---"
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo "unknown")
    pass "NVIDIA GPU: $GPU_NAME"

    if command -v nvidia-container-runtime >/dev/null 2>&1; then
        pass "nvidia-container-toolkit installed"
    else
        warn "nvidia-container-toolkit not installed — GPU in containers won't work"
    fi

    # Quick GPU passthrough test
    if docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
        pass "GPU passthrough working in Docker"
    else
        warn "GPU passthrough failed — check nvidia-container-toolkit setup"
    fi
elif [[ "$(uname -s)" == "Darwin" ]]; then
    # macOS — no NVIDIA, check for Apple Silicon
    CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "unknown")
    pass "macOS detected: $CHIP (Docker runs CPU-only)"
else
    warn "No NVIDIA GPU detected — containers will use CPU only"
fi

# ── 7. Ollama ──────────────────────────────────────────────────────────────
echo ""
echo "--- Ollama ---"
if command -v ollama >/dev/null 2>&1; then
    OVER=$(ollama --version 2>&1 || echo "unknown")
    pass "Ollama installed: $OVER"
    if ollama list >/dev/null 2>&1; then
        MODEL_COUNT=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
        pass "Ollama running, $MODEL_COUNT model(s) available"
    else
        warn "Ollama not running — start with: ollama serve"
    fi
else
    warn "Ollama not installed locally — will run in Docker container"
fi

# ── 8. Python (local, for non-Docker usage) ────────────────────────────────
echo ""
echo "--- Python (local) ---"
if [ -x ".venv/bin/python" ]; then
    PYVER=$(.venv/bin/python --version 2>&1)
    pass "venv Python: $PYVER"

    if .venv/bin/python -c "import larry_paths; print(f'v{larry_paths.__version__}')" 2>/dev/null; then
        pass "larry_paths imports OK"
    else
        fail "larry_paths import failed"
    fi
elif command -v python3 >/dev/null 2>&1; then
    PYVER=$(python3 --version 2>&1)
    pass "System Python: $PYVER"
else
    warn "No Python 3 found locally — Docker will still work"
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo -e "  Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${WARN} warnings${NC}"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}Fix the failures above before deploying.${NC}"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "${YELLOW}Warnings are non-blocking but should be addressed.${NC}"
    exit 0
else
    echo -e "${GREEN}All checks passed! Ready to deploy.${NC}"
    exit 0
fi
