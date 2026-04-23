# Agent Larry (G-FORCE)

**A fully local, multi-model AI agent with GPU acceleration, cross-platform remote execution, security monitoring, and production RAG — all running on localhost with zero cloud dependencies.**

Built for: Ubuntu 24.04 + NVIDIA RTX 4060 8GB + 64GB DDR5 RAM + NordVPN Meshnet to Win11Pro

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Hardware Requirements](#hardware-requirements)
- [Quick Start (New Machine)](#quick-start-new-machine)
- [Installed Models](#installed-models)
- [Model Routing](#model-routing)
- [Hardware Profiles](#hardware-profiles)
- [Slash Commands Reference](#slash-commands-reference)
- [MCP Servers](#mcp-servers)
- [Security Tools](#security-tools)
- [Dashboard](#dashboard)
- [Robin Remote Runner (Win11)](#robin-remote-runner-win11)
- [Security Sentinel](#security-sentinel)
- [RAG (Retrieval Augmented Generation)](#rag-retrieval-augmented-generation)
- [Voice Module](#voice-module)
- [Multi-Line Input](#multi-line-input)
- [Gaming VRAM Coexistence](#gaming-vram-coexistence)
- [Network & Firewall](#network--firewall)
- [File Structure](#file-structure)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
Ubuntu 24.04 (primary)                         Win11Pro (remote)
+--------------------------------------------+ +------------------------+
| agent_v2.py (interactive REPL)             | | robin_remote_server.py |
|   +-- model_router.py (task routing)       | | FastAPI on Meshnet     |
|   +-- hardware_profiles.py (SPEED/ACC/..)  | | 100.88.131.215:7341    |
|   +-- production_rag.py (ChromaDB + BAAI)  | | bearer-token auth      |
|   +-- mcp_client.py (9 native MCP servers) | +----------^-------------+
|   +-- kali_tools.py (security toolkit)     |            |
|   +-- agent_tools.py (tool-calling loop)---+--Meshnet---+
|   +-- web_tools.py (scrape/search/youtube) |
|   +-- file_browser.py + sandbox_manager.py |
|   +-- voice_module.py (STT/TTS)           |
+--------------------------------------------+
| dashboard_hub.py  (Flask UI :3777)         |
| security_sentinel.py (15-min threat cycle) |
| telegram_bot.py (remote queries + alerts)  |
+--------------------------------------------+
| Ollama (GPU-accelerated, :11434 localhost)  |
| 25 models, task-based routing               |
+--------------------------------------------+
```

**Everything runs on 127.0.0.1 except:**
- Robin remote runner over NordVPN Meshnet (peer-to-peer, no internet)
- SSH (port 22, rate-limited)

---

## Hardware Requirements

### Minimum
| Component | Spec |
|-----------|------|
| OS | Ubuntu 22.04+ / Windows 11 (remote only) |
| CPU | 8+ cores (12th gen Intel or Ryzen 5000+) |
| RAM | 32GB DDR4 (64GB DDR5 recommended) |
| GPU | NVIDIA RTX 3060 6GB+ (CUDA 12+) |
| Disk | 100GB free (models are 2-42GB each) |
| Python | 3.11 or 3.12 (3.12.7 tested) |

### Tested On
| Component | Spec |
|-----------|------|
| CPU | Intel (64GB DDR5) |
| GPU | NVIDIA RTX 4060 8GB, power-capped to 100W |
| OS | Ubuntu 24.04, kernel 6.17 |
| Python | 3.12.7 via pyenv |
| NVIDIA Driver | 590.48.01, CUDA 13.1 |
| Ollama | Latest, GPU-accelerated |

---

## Quick Start (New Machine)

### 1. Install system dependencies

```bash
# Python 3.12 via pyenv
curl https://pyenv.run | bash
pyenv install 3.12.7
pyenv global 3.12.7

# NVIDIA drivers + CUDA (Ubuntu)
sudo apt install nvidia-driver-590 nvidia-cuda-toolkit

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Clone and install

```bash
git clone <your-repo-url> ~/Documents/Agent-Larry
cd ~/Documents/Agent-Larry
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)
```

### 4. Pull essential models

```bash
# Minimum viable set (fast + capable)
ollama pull dolphin-mistral:latest       # 4.1GB  - default chat (uncensored)
ollama pull qwen2.5:7b-instruct         # 4.7GB  - general purpose
ollama pull nomic-embed-text:latest      # 274MB  - embeddings for RAG

# Recommended additions
ollama pull qwen3-coder:30b             # 18GB   - coding tasks
ollama pull devstral-small-2:24b        # 15GB   - development
ollama pull dolphin-mixtral:8x7b        # 26GB   - CLI default
ollama pull llama3.2:latest             # 2.0GB  - fast fallback
ollama pull mistral:latest              # 4.4GB  - general purpose

# Large models (need 64GB RAM for CPU layers)
ollama pull llama3.3:70b               # 42GB   - flagship
ollama pull qwen2.5:32b-instruct       # 19GB   - advanced reasoning
ollama pull glm-4.7-flash:latest       # 19GB   - 131K context
```

### 5. Configure GPU offload

```bash
# Create Ollama override for GPU acceleration
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null << 'EOF'
[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=5m"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_ORIGINS=*"
Restart=always
RestartSec=5
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 6. Set GPU safety limits

```bash
sudo nvidia-smi -pm 1       # persistence mode (faster loads)
sudo nvidia-smi -pl 100     # power cap 100W (adjust for your card)
```

### 7. Run the agent

```bash
cd ~/Documents/Agent-Larry
python3 agent_v2.py
```

---

## Installed Models

Models currently pulled on the reference system. Pull only what you need.

### Tier 1 - Flagship (need 64GB RAM)
| Model | Size | Context | Best For |
|-------|------|---------|----------|
| llama3.3:70b | 42GB | 131K | Everything — best quality |
| qwen3-coder:30b | 18GB | 32K | Code generation, refactoring |
| qwen2.5:32b-instruct | 19GB | 32K | Reasoning, analysis |
| glm-4.7-flash:latest | 19GB | 131K | Ultra-long context |
| dolphin-mixtral:8x7b | 26GB | 32K | CLI default, uncensored |

### Tier 2 - Medium (16-32GB RAM)
| Model | Size | Context | Best For |
|-------|------|---------|----------|
| devstral-small-2:24b | 15GB | 32K | Development tasks |
| qwen2.5:14b-instruct-q4_K_M | 9.0GB | 32K | Balanced reasoning |
| ministral-3:14b | 9.1GB | 32K | Fast general purpose |
| dolphincoder:15b | 9.1GB | 16K | Coding focus |
| mistral-nemo:latest | 7.1GB | 128K | Long context chat |

### Tier 3 - Fast (8-16GB RAM)
| Model | Size | Context | Best For |
|-------|------|---------|----------|
| qwen2.5:7b-instruct | 4.7GB | 32K | Quick answers |
| dolphin-mistral:latest | 4.1GB | 32K | Fast chat, uncensored |
| mistral:latest | 4.4GB | 32K | General purpose |
| ministral-3:latest | 6.0GB | 32K | Fast general |
| qwen2.5-128k:latest | 5.4GB | 128K | Long docs |

### Tier 4 - Tiny (<4GB RAM)
| Model | Size | Context | Best For |
|-------|------|---------|----------|
| llama3.2:latest | 2.0GB | 4K | Instant responses |
| granite4:1b | 3.3GB | 4K | Minimal resource |
| lfm2.5-thinking:1.2b | 731MB | 4K | Reasoning on a budget |

### Embedding & Vision
| Model | Size | Purpose |
|-------|------|---------|
| nomic-embed-text:latest | 274MB | RAG embeddings (8K context) |
| minicpm-v:latest | 5.5GB | Vision-language |
| glm-ocr:latest | 2.2GB | OCR / document reading |

---

## Model Routing

The agent automatically selects the best model based on your query. Override with `/model <name>` or use `/model auto` to re-enable routing.

| Query Type | Detection Keywords | Preferred Models |
|------------|-------------------|-----------------|
| **Coding** | code, function, debug, python, refactor, bug | qwen3-coder:30b, devstral, dolphincoder |
| **Reasoning** | explain, analyze, logic, step by step, why | deepseek-r1, llama3.3, qwen2.5:32b |
| **Chat** | (default fallback) | dolphin-mistral, llama3.2, mistral |
| **Creative** | story, poem, generate, creative, write | dolphin-mixtral, dolphin-mistral |
| **Summarize** | summarize, summary, tldr, brief | llama3.2, mistral, ministral |
| **Vision** | image, picture, describe, screenshot | minicpm-v, llava, qwen3-vl |
| **Analysis** | analyze, compare, evaluate, assess | qwen2.5:32b, llama3.3 |
| **Agentic** | (autonomous mode) | dolphin-mixtral, llama3.3 |

Routing falls through priority chains: if the top model isn't pulled, the next one in line is used.

---

## Hardware Profiles

Switch with `/profile <name>`. Default is `ACCURACY`.

| Profile | Context | GPU Layers | Threads | Temp | Use Case |
|---------|---------|-----------|---------|------|----------|
| `SPEED` | 16K | 33 (full GPU) | auto | 0.7 | Quick answers, small tasks |
| `BALANCED` | 32K | 20 | 8 | 0.5 | General purpose |
| `ACCURACY` | 65K | 15 | 12 | 0.3 | Detailed analysis (default) |
| `ULTRA_CONTEXT` | 131K | 8 | 16 | 0.3 | Full-file analysis, large docs |

GPU layers control how much of the model is on GPU vs CPU RAM. More GPU layers = faster but uses more VRAM.

---

## Slash Commands Reference

### System
| Command | Description |
|---------|-------------|
| `/quit`, `/exit`, `/q` | Exit agent |
| `/help`, `/h`, `/?` | Show help |
| `/models` | List available Ollama models |
| `/model <name>` | Switch model (or `auto` for routing) |
| `/profile <name>` | Switch hardware profile |
| `/stats` | Show statistics |
| `/clear` | Clear conversation history |
| `/history` | Show last 10 messages |
| `/context` | Show context usage and token stats |
| `/tokens [text]` | Count tokens |

### File Operations
| Command | Description |
|---------|-------------|
| `/ls [path]` | List directory |
| `/cd <path>` | Change directory |
| `/pwd` | Print working directory |
| `/tree [path] [depth]` | Directory tree |
| `/cat <file> [start] [end]` | Read file with smart formatting |
| `/find <pattern> [path] [-c]` | Find files (`-c` searches content) |
| `/grep <pattern> <file>` | Search in file |
| `/edit <file> <start> <end> <content>` | Edit lines in file |
| `/open <file> [--diff] [--yes]` | Open in editor |
| `/write <file> <content> [--yes]` | Write to file |
| `/csv-edit <file> <key> <val> <col> <new>` | Edit CSV rows |
| `/run <script>` | Execute .py/.ps1/.bat |

### Web & Search
| Command | Description |
|---------|-------------|
| `/web <url>` | Scrape and index web page |
| `/scrape <url>` | Scrape to markdown |
| `/search_web <query>` | Brave Search (needs API key) |
| `/youtube <url>` | YouTube transcript + summary |

### RAG & Knowledge
| Command | Description |
|---------|-------------|
| `/index <dir> [limit]` | Index directory for RAG |
| `/rag <question>` | Ask about indexed codebase |
| `/ask <question>` | Alias for /rag |
| `/search <query>` | Search knowledge base |
| `/memory` | Knowledge graph (show/search/add) |

### Sandbox (Safe Edit)
| Command | Description |
|---------|-------------|
| `/sandbox stage <file>` | Stage file for editing |
| `/sandbox edit <file> <text>` | Edit in sandbox |
| `/sandbox test <file>` | Test changes |
| `/sandbox deploy <file>` | Deploy with backup |
| `/sandbox rollback <file>` | Rollback to backup |

### Agentic Mode
| Command | Description |
|---------|-------------|
| `/agent <task>` | Autonomous multi-step task execution |

### Security
| Command | Description |
|---------|-------------|
| `/tools [category]` | List security tools |
| `/kali <tool> [args]` | Run Kali tool (nmap, nikto, sqlmap...) |
| `/kali list [category]` | List tools by category |
| `/security [subcmd]` | Security Command Center |
| `/investigate`, `/ports` | Port investigation |
| `/hunt` | Network host discovery |

### Voice
| Command | Description |
|---------|-------------|
| `/voice` | Voice module status |
| `/speak <text>` | Text-to-speech |
| `/listen` | Voice input mode |
| `/transcribe <file>` | Transcribe audio |

### Skills & MCP
| Command | Description |
|---------|-------------|
| `/skill [name]` | List or activate skill profile |
| `/mcp` | Show MCP tools status |
| `/github`, `/gh` | GitHub operations |

---

## MCP Servers

Native Python MCP servers — no Docker required.

| Server | Status | Description |
|--------|--------|-------------|
| **filesystem** | enabled | Read, write, list, search files (sandboxed) |
| **memory** | enabled | Knowledge graph: entities, relations |
| **sqlite** | enabled | Database queries and schema |
| **brave-search** | enabled | Web search (needs `BRAVE_API_KEY`) |
| **playwright** | enabled | Browser automation, screenshots |
| **context7** | enabled | Library documentation lookup |
| **time** | enabled | Date/time, timezone conversion |
| **github** | enabled | GitHub API (needs `GITHUB_TOKEN`) |
| **n8n** | disabled | Workflow automation (needs n8n running) |
| **podman** | disabled | Container management |
| **desktop-commander** | disabled | Desktop automation |

Config: `mcp.json`

---

## Security Tools

### Kali Integration
Wraps standard penetration testing tools with presets and timeouts:

| Category | Tools |
|----------|-------|
| **Recon** | nmap, nikto, whatweb, fierce, dnsrecon, dnsenum |
| **Web** | dirsearch, sqlmap, wpscan, nuclei |
| **Crypto** | hashcat, hydra, john |
| **Network** | tcpdump, wireshark, airodump-ng |

**Nmap presets:** `quick`, `full`, `service`, `vuln`, `udp`, `os`

### Security Command Center
| Command | Description |
|---------|-------------|
| `investigate [target]` | Port investigation with geolocation |
| `hunt [network]` | Network host discovery |
| `traffic [iface]` | Traffic analysis |
| `firewall [test]` | Firewall rule testing |
| `full-audit [target]` | Complete security audit |
| `quick` | Fast overview |

---

## Dashboard

**Flask web UI** at `http://127.0.0.1:3777` (localhost only)

Pages: System Health, AI Models, RAG Knowledge, Security Center, Network Monitor, Service Control, Settings.

```bash
# Start manually
python3 dashboard_hub.py --no-browser

# Auto-starts via GNOME autostart or systemd
```

---

## Robin Remote Runner (Win11)

Execute scripts on a Windows machine over NordVPN Meshnet. The Win11 machine runs a FastAPI server authenticated with a bearer token.

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ping` | Health check |
| GET | `/list_jobs` | List background jobs |
| POST | `/run_script` | Execute script (timeout: 120s) |
| POST | `/start_background` | Start background job |
| POST | `/stop_background` | Kill background job |
| POST | `/health_check` | Check target health |

### Setup on Win11
1. Install Python 3.12+ and NordVPN with Meshnet enabled
2. Transfer `robin_remote_server.py` via `nordvpn fileshare send` (NOT clipboard — it corrupts files)
3. Create token: `python -c "import secrets; open(r'C:\Users\YOU\.robin\token','w').write(secrets.token_hex(32))"`
4. Copy same token to Ubuntu: `~/.robin/remote_token`
5. Create scheduled task for auto-start on login (use `pythonw.exe` for headless)
6. Add Windows firewall rule: `New-NetFirewallRule -DisplayName 'Robin' -Direction Inbound -Protocol TCP -LocalPort 7341 -RemoteAddress 100.64.0.0/10 -Action Allow`

### Verify from Ubuntu
```bash
curl -H "Authorization: Bearer $(cat ~/.robin/remote_token)" http://100.88.131.215:7341/ping
# {"ok":true,"host":"win11","time":...}
```

### Security
- Bearer token authentication (401/403 on failure)
- Path allow-list: only scripts under designated directories
- Script type restriction: `.py` and `.bat` only
- Meshnet-only binding (not internet-reachable)

---

## Security Sentinel

Background watchdog running a 15-minute threat monitoring cycle.

### What it monitors
- New listening ports (alert on unexpected services)
- Failed SSH logins (from auth log)
- Suspicious processes (high CPU/memory, unknown binaries)
- Network connections (new outbound, geolocation anomalies)
- File integrity (hash changes in critical configs)
- Resource pressure (disk >95%, memory >92%, CPU >90%)
- VPN status changes

### Alerts
- Sent to Telegram with MD5-based dedup (10-min TTL)
- State transitions: alert -> clear triggers "all clear" notification
- Resource budget: <200MB VRAM, <2% CPU

### Config
- `telegram_bot` respawn is **disabled** (set `restart_cmd: None` in WATCHED_SERVICES)
- Dashboard and agent are still auto-restarted
- Edit `security_sentinel.py` WATCHED_SERVICES dict to change behavior

---

## RAG (Retrieval Augmented Generation)

### How it works
1. `/index <directory>` — chunks files, generates embeddings via Ollama, stores in ChromaDB
2. `/rag <question>` — embeds your question, searches ChromaDB, reranks with BAAI, builds context for the model

### Config (in `larry_config.json`)
| Setting | Value | Description |
|---------|-------|-------------|
| backend | chroma | ChromaDB vector store |
| embedding_model | nomic-embed-text | Ollama local embeddings |
| chunk_size | 800 | Characters per chunk |
| chunk_overlap | 250 | Overlap between chunks |
| reranker_model | BAAI/bge-reranker-v2-m3 | GPU-accelerated reranker |

### Production RAG (`production_rag.py`)
Uses `mxbai-embed-large` for higher quality embeddings and a two-stage retrieve-then-rerank pipeline.

---

## Voice Module

Optional — requires additional dependencies.

| Feature | Description |
|---------|-------------|
| STT | Speech-to-text via Whisper |
| TTS | Text-to-speech via local TTS engine |
| Voice cloning | Clone voice from audio sample |

Enable in `larry_config.json`: `"voice_enabled": true`

---

## Multi-Line Input

To paste large files or multi-line content, type `<<<` (or `"""` or `'''`), paste your content, then type the same delimiter on its own line:

```
You: <<<
  (multi-line mode)
[paste entire file here]
<<<
```

No length limit on input.

---

## Gaming VRAM Coexistence

The agent is configured to share GPU with gaming:

| Setting | Value | Effect |
|---------|-------|--------|
| `OLLAMA_KEEP_ALIVE` | 5m | Model auto-unloads 5 min after last query |
| `OLLAMA_MAX_LOADED_MODELS` | 1 | Only one model in VRAM at a time |
| GPU power cap | 100W | Thermal headroom for gaming |

### Before launching a game
```bash
# Instant VRAM release (~4-5GB freed)
ollama stop dolphin-mistral

# Or just wait 5 minutes after your last query
```

### VRAM usage reference
| Model | VRAM | Fits with gaming? |
|-------|------|-------------------|
| llama3.2:latest (2GB) | ~2.5GB | Yes - leaves 5.5GB |
| dolphin-mistral (4.1GB) | ~4.8GB | Tight - stop before gaming |
| qwen2.5:7b (4.7GB) | ~5.5GB | No - stop before gaming |
| Anything >7GB | CPU offload | VRAM not affected |

---

## Network & Firewall

### Ubuntu UFW Rules
```
Default: deny incoming, allow outgoing
Loopback: ALLOW
SSH (22/tcp): LIMIT (rate-limited)
Ports 11434, 3777, 7341: DENY inbound (defense-in-depth)
NordLynx interface: DENY all service ports (anti-VPN-leak)
```

### Listening Services (all localhost)
| Service | Bind Address | Port |
|---------|-------------|------|
| Ollama | 127.0.0.1 | 11434 |
| Dashboard | 127.0.0.1 | 3777 |
| Telegram bot | (no port) | outbound polling |
| Agent REPL | (no port) | terminal stdin |

### Why no TLS on localhost
Localhost traffic never leaves the machine. UFW blocks any external packet claiming a loopback source. TLS on 127.0.0.1 is security theater.

---

## File Structure

```
Agent-Larry/
+-- agent_v2.py                 # Main interactive agent (entry point)
+-- model_router.py             # Task-based model selection
+-- hardware_profiles.py        # SPEED/BALANCED/ACCURACY/ULTRA_CONTEXT
+-- skill_manager.py            # Dynamic skill registration
+-- larry_config.json           # Main configuration
+-- mcp.json                    # MCP server configuration
+-- .env                        # API keys and secrets (not committed)
+-- requirements.txt            # Python dependencies
|
+-- dashboard_hub.py            # Flask web dashboard (:3777)
+-- security_sentinel.py        # Background threat monitor
+-- telegram_bot.py             # Telegram bot integration
+-- robin_remote_server.py      # Win11 remote runner (FastAPI)
+-- agent_tools.py              # Tool-calling loop + scheduler
|
+-- production_rag.py           # ChromaDB + Ollama embeddings + BAAI reranker
+-- rag_integration.py          # Legacy RAG layer
+-- mcp_client.py               # Native MCP client (9 servers)
+-- web_tools.py                # Web scraping, YouTube, search
+-- kali_tools.py               # Security tool wrappers
|
+-- file_browser.py             # Safe file operations
+-- sandbox_manager.py          # Stage/edit/test/deploy workflow
+-- token_manager.py            # Token counting (tiktoken)
+-- universal_file_handler.py   # CSV, Excel, PDF handling
+-- cross_platform_paths.py     # Windows/Linux path management
|
+-- security_command_center.py  # Unified security CLI
+-- port_investigator.py        # Connection intelligence
+-- network_hunter_tools.py     # Host discovery
+-- traffic_analyzer.py         # Traffic analysis
|
+-- voice_module.py             # STT/TTS/voice cloning
+-- voice_chat.py               # Voice conversation interface
+-- activity_stream.py          # JSONL event bus
+-- session_manager.py          # Session persistence
+-- resource_governor.py        # CPU/memory/VRAM management
|
+-- scripts/
|   +-- harden_local_ports.sh   # UFW hardening script
|   +-- nordvpn-up-watcher.sh   # Meshnet status monitor
|
+-- data/                       # Runtime data (SQLite, history)
+-- chroma_db/                  # ChromaDB vector store
+-- logs/                       # Application logs
+-- sandbox/                    # Sandbox staging area
+-- memory.json                 # Knowledge graph
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Required
OLLAMA_HOST=http://localhost:11434

# Recommended
TELEGRAM_BOT_TOKEN=<your-bot-token>          # From @BotFather
TELEGRAM_ALLOWED_CHAT_IDS=<your-chat-id>     # From @userinfobot
BRAVE_API_KEY=<your-brave-api-key>           # From brave.com/search/api

# Optional
GITHUB_TOKEN=<your-github-pat>               # For GitHub MCP server
HF_TOKEN=<your-huggingface-token>            # For model downloads
OPENROUTER_API_KEY=<key>                     # Cloud model fallback

# Telemetry (all disabled)
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY=False
DO_NOT_TRACK=1
```

---

## Troubleshooting

### Ollama not using GPU
```bash
# Check if CUDA is detected
nvidia-smi
# Check Ollama config
cat /etc/systemd/system/ollama.service.d/override.conf
# CUDA_VISIBLE_DEVICES must be "0", NOT empty ""
# Restart after changes
sudo systemctl daemon-reload && sudo systemctl restart ollama
# Verify GPU usage
curl -s http://127.0.0.1:11434/api/ps | python3 -m json.tool
# size_vram should be > 0
```

### Model too slow
```bash
# Check if model fits in VRAM (8GB)
# Models <6GB run fully on GPU, larger ones spill to CPU RAM
/profile SPEED   # in agent — uses all GPU layers
```

### Dashboard won't start
```bash
python3 dashboard_hub.py --no-browser
# Check if port 3777 is in use: ss -tlnp | grep 3777
```

### Robin remote runner not responding
```bash
# From Ubuntu
curl -H "Authorization: Bearer $(cat ~/.robin/remote_token)" http://100.88.131.215:7341/ping
# Check Win11: is pythonw.exe running? Is NordVPN Meshnet connected?
# On Win11 PowerShell: Get-NetTCPConnection -LocalPort 7341
```

### VRAM full / out of memory
```bash
ollama stop dolphin-mistral   # or whatever model is loaded
nvidia-smi                     # verify VRAM freed
# Reduce OLLAMA_MAX_LOADED_MODELS to 1 in override.conf
```

### Sentinel keeps restarting telegram_bot
Edit `security_sentinel.py`, find `WATCHED_SERVICES["telegram_bot"]`, set `"restart_cmd": None`.

---

## License

MIT
