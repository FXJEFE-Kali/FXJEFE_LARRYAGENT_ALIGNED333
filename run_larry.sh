#!/usr/bin/env bash
# run_larry.sh — portable launcher for Agent Larry (Linux / macOS).
#
# Works from any location — local install, USB stick, network share.
# Anchors all paths to the directory containing this script; no hardcoded
# absolute paths anywhere. If a .venv/ is shipped alongside the project it
# is used automatically; otherwise falls back to the first `python3` on PATH.
#
# Usage:
#   ./run_larry.sh                 # launch agent_v2.py interactive CLI
#   ./run_larry.sh dashboard       # launch dashboard_hub.py
#   ./run_larry.sh paths           # print resolved paths (debug)
#   ./run_larry.sh <script.py> ... # run any project script with venv activated
set -euo pipefail

# Resolve the directory of this script, following symlinks — classic portable pattern.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
LARRY_HOME="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
export LARRY_HOME

cd "$LARRY_HOME"

# Pick a Python interpreter. Priority:
#   1. bundled venv   (.venv/bin/python) — ships with the project
#   2. $LARRY_PYTHON  (manual override)
#   3. python3 on PATH
if [ -x "$LARRY_HOME/.venv/bin/python" ]; then
    PY="$LARRY_HOME/.venv/bin/python"
elif [ -n "${LARRY_PYTHON:-}" ] && [ -x "$LARRY_PYTHON" ]; then
    PY="$LARRY_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
else
    echo "ERROR: no python3 found. Install Python 3.10+ or set \$LARRY_PYTHON." >&2
    exit 1
fi

# Ensure the project root is on PYTHONPATH so relative imports work from any CWD.
export PYTHONPATH="$LARRY_HOME${PYTHONPATH:+:$PYTHONPATH}"

# Quiet mode for tokenizers / transformers when running from USB (no write cache).
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

case "${1:-}" in
    ""|agent|cli)
        exec "$PY" "$LARRY_HOME/agent_v2.py" "${@:2}"
        ;;
    dashboard|hub)
        exec "$PY" "$LARRY_HOME/dashboard_hub.py" "${@:2}"
        ;;
    paths|where)
        exec "$PY" "$LARRY_HOME/larry_paths.py"
        ;;
    telegram)
        exec "$PY" "$LARRY_HOME/telegram_bot.py" "${@:2}"
        ;;
    status)
        echo "=== Agent Larry Status ==="
        "$PY" -c "from larry_paths import __version__; print(f'Version: {__version__}')" 2>/dev/null || echo "Version: unknown"
        echo ""
        echo "--- Python ---"
        echo "Interpreter: $PY"
        "$PY" --version 2>&1
        echo ""
        echo "--- Ollama ---"
        if command -v ollama >/dev/null 2>&1; then
            ollama --version 2>&1 || true
            echo "Models:"
            ollama list 2>/dev/null | head -10 || echo "  (not running)"
        else
            echo "  Not installed"
        fi
        echo ""
        echo "--- GPU ---"
        if command -v nvidia-smi >/dev/null 2>&1; then
            nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "  No GPU detected"
        elif command -v system_profiler >/dev/null 2>&1; then
            system_profiler SPDisplaysDataType 2>/dev/null | grep -E "Chipset|VRAM|Metal" | head -5
        else
            echo "  No GPU info available"
        fi
        echo ""
        echo "--- Docker ---"
        if command -v docker >/dev/null 2>&1; then
            docker --version 2>&1
            echo "Containers:"
            docker ps --filter "name=larry-" --format "  {{.Names}}: {{.Status}}" 2>/dev/null || echo "  (none running)"
        else
            echo "  Not installed"
        fi
        echo ""
        echo "--- MCP Servers ---"
        "$PY" -c "from mcp_servers import registry; print(f'Loaded: {len(registry)} — {list(registry.keys())}')" 2>/dev/null || echo "  Error loading"
        exit 0
        ;;
    -h|--help|help)
        cat <<EOF
Agent Larry portable launcher

Usage: $(basename "$0") [command] [args...]

Commands:
  agent, cli       Launch agent_v2.py interactive CLI (default)
  dashboard, hub   Launch dashboard_hub.py web UI
  telegram         Launch telegram_bot.py
  status           Show running services, GPU, models, MCP servers
  paths, where     Print resolved project paths and exit
  <script.py>      Run any project script with venv activated
  help             Show this message

Env vars:
  LARRY_HOME       Override project root (defaults to script directory)
  LARRY_PYTHON     Path to Python interpreter (overrides auto-detect)
  OLLAMA_URL       Ollama API URL (default: http://localhost:11434/api/chat)
EOF
        exit 0
        ;;
    *)
        # Run any script/module under the project root.
        if [ -f "$LARRY_HOME/$1" ]; then
            exec "$PY" "$LARRY_HOME/$1" "${@:2}"
        else
            exec "$PY" "$@"
        fi
        ;;
esac
