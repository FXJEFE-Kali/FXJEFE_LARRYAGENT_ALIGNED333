# UNIFIED SETUP GUIDE
## Consolidated Agent-Larry System (v2.0)

**Last Updated:** 2025 | **Status:** Phase 5-6 Complete | **Maintainer:** Agent-Larry System

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Core Modules](#core-modules)
7. [Skill System](#skill-system)
8. [MCP Infrastructure](#mcp-infrastructure)
9. [Configuration Management](#configuration-management)
10. [Telegram Integration](#telegram-integration)
11. [RAG System](#rag-system)
12. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

Agent-Larry is a **unified AI agent platform** built on:
- **Python 3.13** with local Ollama inference
- **Skill-based architecture** (12+ extensible skills)
- **MCP infrastructure** (Model Context Protocol - 8+ native servers)
- **Configuration-driven design** (JSON-based, runtime-reloadable)
- **Production RAG** (retrieval-augmented generation pipeline)
- **Optional Telegram integration** (real-time notifications & commands)

### Key Features

✅ **Config Management** - Dynamic profile switching (SPEED/BALANCED/ACCURACY)
✅ **MCP Toolkit** - 8+ native servers (filesystem, memory, git, brave search, etc.)
✅ **Production RAG** - Hybrid search with embeddings + BM25 ranking
✅ **Skills System** - Extensible command registry with real-time execution
✅ **Modular Architecture** - Import only what you need
✅ **Error Resilience** - Graceful degradation when components unavailable

---

## ARCHITECTURE

```
Agent-Larry System (v2.0)
├── ENTRY POINTS
│   ├── agent_v2.py (CLI agent interface with Ollama)
│   ├── telegram_bot.py (Telegram interface with device tracking)
│   └── FastAPI web endpoints (future: REST API)
│
├── SKILL SYSTEM
│   ├── SkillManager (skill registry & execution)
│   ├── Config Skills (4 skills: config, model_profile, rag_settings, reload_config)
│   ├── MCP Skills (4 skills: mcp_list, mcp_status, mcp_enable, mcp_disable)
│   ├── System Skills (hello_world, system_health, quick_backup, skill_stats, agent_uptime, ...)
│   └── Integration Skills (telegram_bot_status, telegram_send_test, list_files)
│
├── CONFIGURATION LAYER
│   ├── larry_config.json (source of truth)
│   ├── .env (secrets management)
│   └── Runtime loader with fallback defaults
│
├── MCP INFRASTRUCTURE
│   ├── mcp_client.py (MCPToolkit with 8+ native servers)
│   ├── FilesystemTools (list, read, write, delete)
│   ├── MemoryTools (persist/retrieve state)
│   ├── DatabaseTools (SQLite queries)
│   ├── SearchTools (Brave Search integration)
│   ├── BrowserTools (Playwright automation)
│   ├── n8nTools (workflow automation)
│   └── PodmanTools (container operations)
│
├── RAG ENGINE
│   ├── production_rag.py (ProductionRAG class)
│   ├── ChromaDB backend (vector storage)
│   ├── Sentence Transformers embeddings (all-MiniLM-L6-v2)
│   ├── BM25 ranking (sparse retrieval)
│   └── Hybrid search orchestration
│
├── UTILITIES
│   ├── web_tools.py (web scraping, content extraction)
│   ├── kali_tools.py (security scanning integration)
│   ├── agent_tools.py (agent-specific utilities)
│   ├── model_router.py (model selection logic)
│   └── activity_stream.py (event logging)
│
└── SUPPORTING FILES
    ├── Dockerfile (containerization)
    ├── docker-compose.yml (orchestration)
    └── requirements*.txt (dependencies)
```

---

## PREREQUISITES

### System Requirements

- **OS:** Linux (Ubuntu 20.04+, CentOS 8+) or macOS 12+
- **Python:** 3.11+ (tested on 3.13)
- **RAM:** 8GB minimum (16GB recommended for accuracy models)
- **GPU:** Optional but recommended (NVIDIA with CUDA 12.x)
- **Disk:** 20GB free (for models, embeddings, ChromaDB)

### Required Software

```bash
# Python 3.13 (or 3.11+)
python3 --version

# Optional but recommended
ollama --version          # Local LLM inference
docker --version          # For containerization
git --version             # For MCP Git tools
```

### API Keys (Optional)

```
BRAVE_API_KEY              # Web search capability
GITHUB_TOKEN               # GitHub MCP tools
HUGGINGFACE_TOKEN          # Model access
TELEGRAM_BOT_TOKEN         # Telegram integration
```

---

## INSTALLATION

### Step 1: Clone/Extract Workspace

```bash
cd ~/Documents/Agent-Larry
# Or: git clone <repo> Agent-Larry
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows PowerShell
```

### Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# OR install extended (with extra tools)
pip install -r requirements-linux.txt

# OR install production-ready
pip install -r requirements-production.txt
```

### Step 4: Run Unified Setup

```bash
chmod +x UNIFIED_SETUP.sh
./UNIFIED_SETUP.sh
```

This will:
- ✓ Validate Python environment
- ✓ Check all core modules load
- ✓ Verify Ollama installation
- ✓ Detect available features
- ✓ Show ready-to-launch commands

---

## CONFIGURATION

### Default Configuration Structure

`larry_config.json`:
```json
{
  "model_profiles": {
    "SPEED": {
      "model": "ministral",
      "context_window": 8192,
      "use_case": "Quick responses"
    },
    "BALANCED": {
      "model": "llama2:13b",
      "context_window": 4096,
      "use_case": "General tasks"
    },
    "ACCURACY": {
      "model": "llama3.3:70b",
      "context_window": 8192,
      "use_case": "Complex reasoning"
    }
  },
  "rag": {
    "enabled": true,
    "backend": "chromadb",
    "model": "all-MiniLM-L6-v2",
    "device": "cuda"
  },
  "mcp": {
    "enabled": true,
    "servers": ["filesystem", "memory", "brave-search", "github", ...]
  }
}
```

### Environment Variables

Create `.env`:
```bash
# Agent Configuration
AGENT_DEBUG=False
AGENT_LOG_LEVEL=INFO

# Model Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.3:70b

# RAG Configuration
RAG_BACKEND=chromadb
RAG_DEVICE=cuda  # or 'cpu'

# MCP Configuration
MCP_TIMEOUT=30
MCP_RETRY_COUNT=3

# API Keys
BRAVE_API_KEY=<your-key>
GITHUB_TOKEN=<your-token>
HUGGINGFACE_TOKEN=<your-token>

# Telegram (optional)
TELEGRAM_BOT_TOKEN=<your-token>
TELEGRAM_CHAT_ID=<your-id>

# Telemetry (privacy)
DO_NOT_TRACK=1
ANONYMIZED_TELEMETRY=False
```

### Runtime Configuration Reload

```bash
# In agent chat:
/skill reload_config        # Reload larry_config.json from disk
/skill config               # Show current configuration
/skill model_profile        # Switch between profiles (SPEED/BALANCED/ACCURACY)
/skill rag_settings         # Show RAG configuration
```

---

## CORE MODULES

### agent_v2.py

**Main agent entry point with skill-based command dispatch.**

```python
# Usage
python agent_v2.py

# In chat, try:
> list all current agent skills           # Built-in early dispatch
> /skill config                           # Show configuration
> /skill model_profile ACCURACY           # Switch to accuracy mode
> /skill mcp_list                         # List MCP servers
> Hello, what can you do?                 # Regular LLM chat
```

**Key Classes:**
- `SkillManager` - Manages skill registry and execution
- `AgentLarry` - Main agent with CLI interface

**Environment:**
- Loads `larry_config.json` at startup
- Lazy-loads MCP toolkit on first use
- Tracks current model profile
- Maintains skill statistics

### mcp_client.py

**MCP infrastructure with 8+ native servers and 50+ tools.**

Available Servers:
- **filesystem** - File operations (list, read, write, delete)
- **memory** - Persistent state (save/load key-value)
- **sqlite** - Database queries
- **brave-search** - Web search
- **playwright** - Browser automation
- **n8n** - Workflow automation
- **podman** - Container operations
- **github** - Git operations

```python
# Usage from agent
toolkit = MCPToolkit()
result = toolkit.call_tool("filesystem", "list_files", {"path": "."})

# Or via skill
/skill mcp_list              # Show all available tools
/skill mcp_status            # Check MCP health
/skill mcp_enable filesystem # Start MCP server
```

### production_rag.py

**Hybrid retrieval-augmented generation with ChromaDB + BM25.**

```python
# Usage
from production_rag import ProductionRAG

rag = ProductionRAG()
results = rag.hybrid_search("query", top_k=5)

# Or via skill
/skill rag_settings          # Show RAG configuration
```

**Features:**
- Vector search (semantic embeddings)
- BM25 ranking (keyword matching)
- Reranking (coherence + relevance scores)
- Metadata filtering
- Device auto-detection (GPU/CPU)

### web_tools.py

**Web scraping and content extraction.**

```python
from web_tools import WebScraper

scraper = WebScraper()
content = scraper.fetch_and_parse("https://example.com")
```

**Features:**
- HTML parsing and cleaning
- JavaScript rendering (optional)
- Content extraction
- Link discovery
- Error resilience

---

## SKILL SYSTEM

### Available Skills (12+)

**System Skills:**
- `hello_world` - Test skill
- `system_health` - System resource monitoring
- `quick_backup` - Backup critical files
- `skill_stats` - Show skill execution statistics
- `agent_uptime` - Show agent uptime
- `list_files` - List workspace files

**Configuration Skills:**
- `config` - Show full configuration
- `model_profile` - Switch between SPEED/BALANCED/ACCURACY
- `rag_settings` - Show RAG configuration
- `reload_config` - Reload configuration from disk

**MCP Skills:**
- `mcp_list` - Enumerate MCP servers and tools
- `mcp_status` - Check MCP server health
- `mcp_enable` - Start MCP server
- `mcp_disable` - Stop MCP server

**Integration Skills:**
- `telegram_bot_status` - Show Telegram bot status
- `telegram_send_test` - Send test message to Telegram
- (expandable list)

### Using Skills in Chat

```bash
# Early dispatch (before LLM)
> list all current agent skills              # Returns skill list

# Skill invocation syntax
> /skill <skill_name> [params]               # Execute skill
> /skill model_profile ACCURACY              # Switch profile
> /skill config                              # Show config
> /skill mcp_list                            # List MCP tools

# Regular chat (after early dispatch)
> Hello, what's your status?                 # Regular LLM response
> Can you help me?                           # Regular LLM response
```

### Adding Custom Skills

See `SKILLMANAGER_GUIDE.md` for details.

---

## MCP INFRASTRUCTURE

### MCP Architecture

```
MCPToolkit (mcp_client.py)
├── MCPClient base class (connection management)
├── 8+ server implementations
│   ├── FilesystemTools (POSIX operations)
│   ├── MemoryTools (state persistence)
│   ├── DatabaseTools (SQLite)
│   ├── SearchTools (Brave Search API)
│   ├── BrowserTools (Playwright)
│   ├── n8nTools (workflow triggers)
│   ├── PodmanTools (container ops)
│   └── GitHubTools (git + API)
└── Tool execution with error handling
```

### MCP Usage Examples

```python
# Get available tools
toolkit = MCPToolkit()
print(toolkit.list_available_tools())

# Call a specific tool
result = toolkit.call_tool(
    "filesystem",
    "list_files",
    {"path": "/home/user", "recursive": True}
)

# Search the web
result = toolkit.call_tool(
    "brave-search",
    "search",
    {"query": "latest AI news"}
)

# Execute shell commands
result = toolkit.call_tool(
    "podman",
    "exec",
    {"container_id": "my_app", "command": "ps aux"}
)
```

### MCP Configuration

In `mcp.json`:
```json
{
  "filesystem": {
    "root_dir": "/home/user",
    "allowed_extensions": [".py", ".json", ".txt"]
  },
  "brave_search": {
    "api_key": "${BRAVE_API_KEY}",
    "max_results": 10
  },
  "github": {
    "token": "${GITHUB_TOKEN}",
    "repos": ["owner/repo1", "owner/repo2"]
  }
}
```

---

## CONFIGURATION MANAGEMENT

### Dynamic Profile Switching

```bash
# View current profile
/skill model_profile            # Shows current (e.g., ACCURACY)

# Switch profile
/skill model_profile SPEED      # Fast mode (ministral)
/skill model_profile BALANCED   # Balanced (llama2:13b)
/skill model_profile ACCURACY   # Accurate (llama3.3:70b)
```

**Profile Details:**

| Profile | Model | Context | Use Case | Speed |
|---------|-------|---------|----------|-------|
| SPEED | ministral | 8K | Quick tasks | ⚡⚡⚡ |
| BALANCED | llama2:13b | 4K | General use | ⚡⚡ |
| ACCURACY | llama3.3:70b | 8K | Complex reasoning | ⚡ |

### Configuration Reload at Runtime

```bash
# Reload from disk (useful after manual edits to larry_config.json)
/skill reload_config

# Show what's currently loaded
/skill config

# Show RAG-specific settings
/skill rag_settings
```

---

## TELEGRAM INTEGRATION

### Setup

1. **Create Telegram Bot** (via @BotFather)
2. **Get Chat ID** (send message to bot, check updates)
3. **Set Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN=<your-bot-token>
   TELEGRAM_CHAT_ID=<your-chat-id>
   ```

4. **Start Bot:**
   ```bash
   python telegram_bot.py
   ```

### Telegram Commands

```
/start              - Initialize bot
/status             - Show system status & device info
/help               - Show available commands
/profile SPEED      - Switch agent profile
/mcp_status         - Show MCP health
/send <message>     - Send message to agent
/backup             - Trigger backup
/logs               - Tail recent logs
```

### Integration with Configuration

- `/profile SPEED|BALANCED|ACCURACY` - Uses config system
- `/mcp_status` - Queries MCP infrastructure
- `/send <msg>` - Routes to agent skills

---

## RAG SYSTEM

### Setup

1. **Ensure ChromaDB is installed:**
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Configure in larry_config.json:**
   ```json
   "rag": {
     "enabled": true,
     "backend": "chromadb",
     "model": "all-MiniLM-L6-v2",
     "device": "cuda",
     "chunk_size": 1000,
     "overlap": 200,
     "collection_name": "agent_knowledge"
   }
   ```

### RAG Usage

```python
from production_rag import ProductionRAG

rag = ProductionRAG()

# Add documents
rag.add_documents([
    {"content": "Document 1", "metadata": {"source": "file1"}},
    {"content": "Document 2", "metadata": {"source": "file2"}}
])

# Search
results = rag.hybrid_search("question about X", top_k=5)
for result in results:
    print(f"Score: {result['score']}, Content: {result['content']}")
```

### View RAG Settings

```bash
/skill rag_settings       # Show current RAG configuration
```

---

## TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'agent_v2'"

**Solution:**
```bash
# Ensure you're in the workspace directory
cd /home/linuxlarry/Documents/Agent-Larry

# Ensure venv is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Ollama connection refused"

**Solution:**
```bash
# Start Ollama service
ollama serve

# Check connection
curl http://localhost:11434/api/tags

# In another terminal, test agent
python agent_v2.py
```

### Issue: MCP Skills Return Empty

**Solution:**
```bash
# Check mcp.json exists
ls -la mcp.json

# Verify MCP tools import
python3 -c "from mcp_client import MCPToolkit; print('OK')"

# Check MCP configuration
/skill mcp_list
/skill mcp_status
```

### Issue: "ChromaDB collection not found"

**Solution:**
```bash
# Reinitialize RAG
python3 -c "from production_rag import ProductionRAG; rag = ProductionRAG(); print('RAG Initialized')"

# Add documents
/skill rag_settings
```

### Issue: Telegram Bot not responding

**Solution:**
```bash
# Verify tokens in .env
grep TELEGRAM .env

# Check bot is running
ps aux | grep telegram_bot

# Restart bot
python telegram_bot.py

# Send test message
/skill telegram_send_test
```

---

## NEXT STEPS

1. **Run UNIFIED_SETUP.sh** to validate your environment
2. **Read SKILLMANAGER_GUIDE.md** for advanced skill development
3. **Explore CONTEXT_INVENTORY.md** for feature reference
4. **Check DOCUMENTATION_INDEX.md** for full catalog

---

## SUPPORT & DOCUMENTATION

- **Quick Ref:** `SKILLMANAGER_CHEATSHEET.md`
- **Full Guide:** `SKILLMANAGER_GUIDE.md`
- **Features:** `CONTEXT_INVENTORY.md`
- **Index:** `DOCUMENTATION_INDEX.md`

---

**Last Updated:** 2025 | **Version:** 2.0 | **System:** Agent-Larry Consolidated
