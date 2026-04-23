# QUICK REFERENCE — Agent-Larry v2.1

## 🚀 START AGENT (Choose One)

```bash
# RECOMMENDED - Universal script (Python)
python START_AGENT.py

# Or shell script (Linux/macOS)
bash start_agent.sh

# Quick validation (no Ollama check)
python START_AGENT.py --quick

# Check only (validate without starting)
python START_AGENT.py --check
```

## ⚙️ BEFORE FIRST RUN

```bash
# 1. Ensure Ollama is running (separate terminal)
ollama serve

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate             # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Edit config
cp larry_config.json larry_config.json.bak
# Edit: larry_config.json
# Edit: .env (optional, for API keys)
```

## 🎮 INTERACTIVE COMMANDS

| Command | Purpose |
|---------|---------|
| `/help` | Show all available commands |
| `/models` | List 25+ available AI models |
| `/tools` | Show security/kali tools |
| `/skill <name>` | Execute a registered skill |
| `/profile` | Show hardware profile (SPEED/ACCURACY/ULTRA_CONTEXT) |
| `/task` | Todo/task manager |
| `/mcp` | MCP server status (8 servers) |
| `/web <query>` | Search the web |
| `/youtube <url>` | Summarize YouTube video |
| `/robin <request>` | Tool-calling loop (real tools) |
| `/agent <task>` | Autonomous agentic mode |
| `/sandbox` | Safe-edit workflow |
| `/history` | Show conversation history |
| `/clear` | Clear conversation |
| `/exit` | Exit agent |

## 📊 STARTUP SEQUENCE

```
1. Environment validation
   ✓ Python 3.10+
   ✓ Virtual environment
   ✓ Directories created
   
2. Module verification
   ✓ All required .py files check
   ✓ Import tests run
   
3. Service checks
   ✓ Ollama availability (HTTP/11434)
   ✓ Database initialization
   ✓ MCP server loading (8 servers)
   
4. Agent initialization
   ✓ Model router (25 models)
   ✓ 20 skills loaded
   ✓ Context manager (65k tokens)
   ✓ File browser ready
   ✓ MCP toolkit started
   
5. Interactive loop started
   → Ready for input
```

## 🔧 CONFIG FILES

| File | Purpose | Edit? |
|------|---------|-------|
| `larry_config.json` | Main agent config | ✏️ YES |
| `.env` | API keys (optional) | ✏️ YES |
| `mcp.json` | MCP servers config | ⚠️ Maybe |
| `requirements.txt` | Python dependencies | ❌ No |

## 📁 DATA DIRECTORIES

Created automatically on startup:

```
data/                   # Persistent storage
  ├─ unified_context.db    # SQLite (65k token context)
  ├─ larry_tasks.json      # Todo items
  ├─ rag_memory.json       # RAG knowledge
  └─ converstion_history.json

chroma_db/              # Vector database (RAG)

sandbox/                # Safe-edit workspace

logs/                   # Startup + execution logs
  └─ startup_*.log      # Latest startup log

voice_cache/            # Cached voice files

context7_cache/         # Library docs cache
```

## 🎯 CORE FEATURES (All Included)

✅ Multi-model support (25+ models)  
✅ File browsing & editing  
✅ Skill system (20 skills)  
✅ MCP toolkit (8 servers)  
✅ Web scraping & search  
✅ Security tools (Kali integration)  
✅ Hardware profiles  
✅ Context management (65k tokens)  
✅ Task/todo tracking  
✅ Sandbox safe-edit  
✅ Voice support (optional)  
✅ Autonomous mode (ReAct)  
✅ Token counting  
✅ Cross-platform paths  
✅ Activity streaming  

## 🚨 COMMON FIXES

**Ollama not accessible?**
```bash
curl http://localhost:11434/api/tags
# If fails, run: ollama serve
```

**Missing modules?**
```bash
pip install -r requirements.txt --force-reinstall
```

**Virtual env issues?**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Python version wrong?**
```bash
python3 --version
# Need 3.10+. Install: sudo apt-get install python3.10
```

**ChromaDB errors?**
```bash
rm -rf chroma_db/
export CHROMA_ALLOW_RESET=TRUE
python START_AGENT.py
```

## 📊 STARTUP OPTIONS

```
python START_AGENT.py              # Full startup
python START_AGENT.py --check      # Validation only
python START_AGENT.py --quick      # Skip Ollama check
python START_AGENT.py --telegram   # Start with Telegram bot
```

## 🔍 CHECK STATUS

```
# During startup
tail -f logs/startup_*.log

# View latest startup log
cat logs/startup_$(ls logs/ | tail -1)

# In agent
/mcp              # MCP server status
/models           # Available models
/tools            # Security tools
```

## 💡 USEFUL ALIASES

Add to `.bashrc` or `.zshrc`:

```bash
alias larry="python ~/Documents/Agent-Larry/START_AGENT.py"
alias larry-check="python ~/Documents/Agent-Larry/START_AGENT.py --check"
alias larry-quick="python ~/Documents/Agent-Larry/START_AGENT.py --quick"
```

Then use:
```bash
larry              # Start agent
larry-check        # Validate
larry-quick        # Quick start
```

---

**For full documentation see**: `STARTUP_GUIDE.md`  
**For agent architecture**: See comments in `agent_v2.py` (3358 lines)  
**For skill development**: Check `skill_manager.py`  
**For MCP server list**: Check `mcp_client.py`
