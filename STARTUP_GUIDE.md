# Agent-Larry v2.1 — Complete Startup Guide

**Version**: 2.1.0 GOD MODE (Fully Featured)  
**Status**: ✅ Production Ready  
**Last Updated**: 2026-04-13

---

## 🚀 Quick Start (TL;DR)

```bash
# Linux/macOS
bash start_agent.sh

# Windows (PowerShell)
python START_AGENT.py

# Validation only (no startup)
python START_AGENT.py --check

# Quick startup (skip Ollama check)
python START_AGENT.py --quick
```

---

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.10 or higher
- **RAM**: 8GB minimum (16GB+ recommended)
- **Disk**: 10GB free space (for models + databases)
- **Network**: Optional (for web scraping, Telegram bot)

### Required Software

#### 1. **Python 3.10+**
```bash
# Check version
python3 --version

# Ubuntu/Debian
sudo apt-get install python3.10 python3.10-venv python3.10-dev

# macOS
brew install python@3.10

# Windows
# Download from python.org
```

#### 2. **Ollama** (Local LLM Engine)
```bash
# Download and install from:
# https://ollama.ai

# Verify installation
ollama --version

# Start Ollama service (leave running in background)
ollama serve
```

**Models to pull (optional but recommended)**:
```bash
ollama pull mistral:7b           # Fast, accurate
ollama pull neural-chat:7b       # Chat optimized
ollama pull qwen:14b            # Fast reasoning
ollama pull codellama:34b       # Code generation
```

#### 3. **Git** (for cloning and version control)
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from git-scm.com
```

---

## 📁 Directory Structure

```
Agent-Larry/
├── START_AGENT.py              # 🔥 NEW: Universal Python startup script
├── start_agent.sh              # 🔥 NEW: Shell startup script (Linux/macOS)
├── agent_v2.py                 # Main agent (3358 lines, fully featured)
├── setup_larry.py              # First-time setup wizard
├── activate_all.py             # Legacy service activation
├── launch_all.py               # Legacy service launcher
│
├── 📁 Core Modules
├── model_router.py             # Model selection & routing
├── file_browser.py             # File operations
├── skill_manager.py            # Skill registration & execution
├── mcp_client.py               # MCP server manager (8 servers)
├── agent_tools.py              # Tool-calling loop (Robin)
├── activity_stream.py          # Event logging
│
├── 📁 AI & RAG
├── unified_context_manager.py  # Context caching (65k tokens)
├── web_tools.py                # Web scraping, search, finance
├── production_rag.py           # Optional: Vector DB RAG
├── rag_integration.py          # Optional: Legacy RAG
│
├── 📁 Security & Operations
├── security_command_center.py  # Security scanning
├── bash_script_runner.py       # Bash execution engine
├── kali_tools.py               # Security tools integration
├── hardware_profiles.py        # Performance profiles
├── sandbox_manager.py          # Safe-edit workflow
├── cross_platform_paths.py     # Path management
│
├── 📁 Optional Features
├── voice_module.py             # Voice input/output (optional: faster-whisper, TTS)
├── telegram_bot.py             # Telegram integration (optional)
├── port_investigator.py        # Network analysis
├── token_manager.py            # Token counting (tiktoken)
│
├── 📁 Data & Config
├── data/                       # Persistent storage
│   ├── unified_context.db      # SQLite context
│   ├── larry_tasks.json        # Task tracker
│   └── rag_memory.json         # RAG memory
├── chroma_db/                  # Vector database
├── sandbox/                    # Sandbox edits
├── logs/                       # Startup/execution logs
│
├── 📁 Configuration
├── larry_config.json           # Agent config (EDIT THIS)
├── mcp.json                    # MCP server config
├── .env                        # Environment secrets
└── requirements.txt            # Python dependencies
```

---

## ⚡ Installation Steps

### Step 1: Clone/Setup Repository

```bash
# Navigate to projects directory
cd ~/Documents

# For new installation
git clone <repo-url> Agent-Larry
cd Agent-Larry

# For existing installation
cd Agent-Larry
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv .venv

# Activate venv
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Verify
which python3  # Should show .venv path
```

### Step 3: Install Dependencies

```bash
# Ensure pip is up to date
pip install --upgrade pip setuptools wheel

# Install requirements (large download ~1GB)
pip install -r requirements.txt

# For production (slimmer)
pip install -r requirements-production.txt

# For GPU support (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Step 4: Configuration

```bash
# Copy example config
cp larry_config.json larry_config.json.bak
# EDIT larry_config.json with your settings

# Copy example .env
cp .env.example .env
# EDIT .env with API keys (optional)

# Verify config
python3 -c "import json; print(json.load(open('larry_config.json')), indent=2)"
```

### Step 5: Start Ollama (Separate Terminal)

```bash
# Terminal 1: Keep Ollama running
ollama serve

# Verify Ollama API is accessible
# Terminal 2:
curl http://localhost:11434/api/tags
```

---

## 🎯 Running the Agent

### Option A: **NEW - Universal Python Starter** ⭐ RECOMMENDED

```bash
# Full startup with all checks
python START_AGENT.py

# Validation only (no startup)
python START_AGENT.py --check

# Skip Ollama check (if not running yet)
python START_AGENT.py --quick

# Alternative: With logging
python START_AGENT.py 2>&1 | tee agent.log
```

**What it does**:
1. ✅ Validates Python, venv, directories
2. ✅ Checks Ollama availability
3. ✅ Verifies all module imports
4. ✅ Initializes databases
5. ✅ Tests MCP servers
6. ✅ Launches agent interactive loop

### Option B: **Shell Script** (Linux/macOS)

```bash
# Make executable (if not already)
chmod +x start_agent.sh

# Full startup
bash start_agent.sh

# Validation only
bash start_agent.sh --check

# Quick startup
bash start_agent.sh --quick
```

### Option C: **Legacy Launchers** (Alternative)

```bash
# Full service orchestration
python activate_all.py                      # Start everything
python activate_all.py --check              # Check status only
python activate_all.py --agent              # Start agent only
python activate_all.py --telegram           # Start with telegram

# Alternative launcher
python launch_all.py

# Or just the agent
python agent_v2.py
```

---

## 📊 Startup Sequence (What Happens)

```
START_AGENT.py (or start_agent.sh)
│
├─ [1] Environment Setup
│  ├─ Validate Python version (3.10+)
│  ├─ Activate virtualenv
│  ├─ Load .env configuration
│  └─ Add project to Python path
│
├─ [2] Directory Validation
│  ├─ Create data/ (persistent storage)
│  ├─ Create logs/ (startup + execution logs)
│  ├─ Create sandbox/ (safe-edit workspace)
│  ├─ Create chroma_db/ (vector database)
│  └─ Create other data directories
│
├─ [3] Module Import Verification
│  ├─ Check all required .py files exist
│  ├─ Try importing critical modules
│  └─ Alert on optional module failures
│
├─ [4] Ollama Service Check
│  ├─ Ping http://localhost:11434/api/tags
│  ├─ List available models
│  └─ Warn if unavailable (non-fatal)
│
├─ [5] Database Initialization
│  ├─ Verify ChromaDB directory
│  ├─ Check SQLite context database
│  └─ Prepare MCP memory stores
│
├─ [6] Agent Initialization
│  ├─ Load model router (25+ models available)
│  ├─ Initialize file browser
│  ├─ Load skill manager (20 skills)
│  ├─ Start MCP toolkit (8 servers)
│  ├─ Initialize all subsystems
│  └─ Load conversation history
│
└─ [7] Interactive Agent Loop
   ├─ Show welcome banner
   ├─ Display available commands
   └─ Wait for user input
```

---

## 🎮 Agent Commands Reference

### Interactive Commands (In Agent)

```
/help                      # Show all commands
/task                      # Task/todo manager
/skill <name>             # Execute a skill
/models                   # List available models
/profile                  # Show/set hardware profile
/mcp                      # MCP server status
/tools                    # Security tools list
/web <query>              # Web search
/youtube <url>            # YouTube summary
/robin <task>             # Tool-calling loop
/agent <task>             # Autonomous agentic mode
/sandbox                  # Safe-edit workflow
/history                  # Show conversation history
/clear                    # Clear conversation
/exit / /quit             # Exit agent
```

### Skills Available (20 Total)

```
system_info              # Show hardware, platform, status
code_review              # Quick code quality check
file_summary             # Analyze file structure
disk_usage               # Check disk space
port_check               # List open ports
security_scan            # Run security audit
[+16 more skills]
```

### Example Interactions

```
> What's my system info?
→ [Uses system_info skill]

> Run a security scan
→ [Uses security_scan skill via kali_tools]

> Review agent_v2.py
→ [Uses code_review skill]

> Search for "machine learning"
→ [Uses web_tools + model routing]

> Debug this Python script
→ [Uses python_debugger_subagent]

> Create a new skill called "weather"
→ [Dynamically creates skill]
```

---

## 🐛 Troubleshooting

### **Issue: "Ollama not accessible"**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If failed, start Ollama in new terminal
ollama serve

# If port conflict, change OLLAMA_HOST
export OLLAMA_HOST="http://localhost:11435"
```

### **Issue: "Module not found"**

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check specific module
python3 -c "import model_router; print('✓ OK')"
```

### **Issue: "Virtual environment not found"**

```bash
# Recreate venv
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### **Issue: "Python version too old"**

```bash
# Check version
python3 --version

# Install Python 3.10+
sudo apt-get install python3.10
python3.10 -m venv .venv
source .venv/bin/activate
```

### **Issue: "Low disk space" warning**

```bash
# Check available space
df -h

# Clean up
rm -rf chroma_db/  # Will be recreated
rm -rf logs/*.log   # Old logs
```

### **Issue: "ChromaDB segfault"**

```bash
# ChromaDB sometimes has issues. Solution:
# 1. Delete the DB (will recreate)
rm -rf chroma_db/

# 2. Set environment variable
export CHROMA_ALLOW_RESET=TRUE

# 3. Restart agent
python START_AGENT.py
```

---

## 🔧 Advanced Configuration

### `larry_config.json`

```json
{
  "agent_name": "LARRY G-FORCE",
  "version": "2.1.0",
  "default_profile": "SPEED",
  "profiles": {
    "SPEED": {
      "num_gpu": 0,
      "num_ctx": 16384,
      "temperature": 0.7
    },
    "ACCURACY": {
      "num_gpu": 0,
      "num_ctx": 65536,
      "temperature": 0.3
    },
    "ULTRA_CONTEXT": {
      "num_gpu": 0,
      "num_ctx": 131072,
      "num_thread": 16
    }
  },
  "features": {
    "voice_enabled": false,
    "mcp_enabled": true,
    "rag_enabled": false,
    "telegram_enabled": false
  }
}
```

### `.env` Secrets (Optional)

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id

# Brave Search
BRAVE_API_KEY=your_key_here

# GitHub
GITHUB_TOKEN=your_token_here

# HuggingFace
HF_TOKEN=your_token_here

# OpenAI (optional, not used by default)
OPENAI_API_KEY=your_key_here
```

---

## 📈 Performance Tuning

### Hardware Profiles

```python
# In agent interactive loop:
/profile ACCURACY      # Most accurate (slower, small context)
/profile SPEED         # Fast responses (16k context)
/profile ULTRA_CONTEXT # Max context (131k tokens, slow)
```

### Model Selection

```bash
# Automatic routing based on task:
Code tasks      → mistral:7b, neural-chat:7b
Reasoning       → qwen:14b, mistral:7b
Long context    → qwen:14b, mistral:7b
Speed required  → neural-chat:7b

# Force specific model:
/model mistral:7b      # Override auto-routing
```

### Context Optimization

```python
# Manages conversation history automatically:
- Keeps last 20 messages
- Limits history to context budget
- Prunes old entries to fit newer queries
```

---

## 🚨 Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t agent-larry:2.1 .

# Run container
docker run -it --name agent-larry \
  -e OLLAMA_HOST=http://ollama:11434 \
  -v $(pwd)/data:/app/data \
  agent-larry:2.1
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/agent-larry.service
[Unit]
Description=Agent-Larry v2.1
After=network.target

[Service]
Type=simple
User=larry
WorkingDirectory=/home/larry/Agent-Larry
ExecStart=/home/larry/Agent-Larry/.venv/bin/python3 START_AGENT.py
Restart=always
Environment="PATH=/home/larry/Agent-Larry/.venv/bin"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable agent-larry
sudo systemctl start agent-larry
sudo systemctl status agent-larry
```

---

## 📊 Startup Checklist

```
[ ] Python 3.10+ installed
[ ] Ollama downloaded and installed
[ ] Virtual environment created
[ ] Dependencies installed (pip install -r requirements.txt)
[ ] larry_config.json configured
[ ] .env configured (if using APIs)
[ ] Ollama service running (ollama serve)
[ ] Startup script validated (python START_AGENT.py --check)
[ ] Agent started successfully
[ ] Commands tested (/help, /models, /tools)
[ ] Custom tasks/skills created
```

---

## 📞 Support

### Get Help In-Agent

```
/help              # Full command reference
/skill <name>      # Help on specific skill
/mcp               # MCP server status
```

### Check Logs

```bash
# Latest startup log
tail -f logs/startup_*.log

# Agent execution log
tail -f logs/agent_log.txt

# Full system log
grep -r "ERROR" logs/
```

### Debug Mode

```bash
# Run with verbose logging
LOGLEVEL=DEBUG python START_AGENT.py

# Or in agent:
/debug on           # Enable debug output
/debug off          # Disable
```

---

## 🎯 Next Steps

1. ✅ **Run**: `python START_AGENT.py`
2. ✅ **Explore**: Type `/help` to see commands
3. ✅ **Customize**: Edit `larry_config.json` for your setup
4. ✅ **Create Skills**: Use `/skill new_skill` to create custom skills
5. ✅ **Extend**: Integrate new tools via MCP servers

---

**Version**: 2.1 GOD MODE (April 13, 2026)  
**Status**: ✅ Production Ready - All Features Working  
**Support**: Check logs/ directory for diagnostic information
