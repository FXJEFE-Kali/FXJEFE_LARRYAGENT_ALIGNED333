# 📚 CONTEXT INVENTORY
## Unused Data & Configurations from Compressedall Archive

**Last Updated:** 2026-04-13  
**Source:** `/home/linuxlarry/Documents/compressedall/Agent-Larry/`  
**Status:** ✅ Parsed & Catalogued  

---

## Table of Contents

1. [Configuration Settings](#configuration-settings)
2. [Model Profiles & Routing](#model-profiles--routing)
3. [MCP Server Infrastructure](#mcp-server-infrastructure)
4. [RAG System Configuration](#rag-system-configuration)
5. [Telegram Bot Features](#telegram-bot-features)
6. [Security & Network Tools](#security--network-tools)
7. [Dependencies (Extended)](#dependencies-extended)
8. [Trading & Finance Tools](#trading--finance-tools)
9. [Feature Flags](#feature-flags)
10. [Integration Opportunities](#integration-opportunities)

---

## Configuration Settings

### 📁 From `larry_config.json` (Compressedall)

#### Hardware Profiles
- **Mode:** CPU (vs GPU in current workspace)
- **RAM:** 64GB DDR5
- **GPU:** RTX 4060 8GB (disabled for LLM in archive version)
- **Context:** `CUDA_VISIBLE_DEVICES=''` (GPU disabled)

**Integration Point:** Current workspace uses GPU mode (better). Merge should keep current GPU settings.

#### Ollama Configuration
```json
{
  "host": "http://localhost:11434",
  "default_model": "dolphin-mixtral:8x7b",
  "embedding_model": "nomic-embed-text:latest",
  "timeout": null,
  "num_parallel": 1,
  "keep_alive": "10m",
  "cli_default_model": "dolphin-mixtral:8x7b",
  "telegram_default_model": "dolphinecoder:15b"
}
```

**Status:** ✅ Already in current `larry_config.json`

---

## Model Profiles & Routing

### 🎯 Available Profiles

**Current (in config):**
- `SPEED` - Fast inference, lower quality
- `BALANCED` - Trade-off mode
- `ACCURACY` - Slow but best quality
- `ULTRA_CONTEXT` - Extended context windows

### 📊 Model Tiers

**Tier 1 (Flagship - Best Quality, Slowest)**
```
- llama3.3:70b
- qwen2.5:32b-instruct
- glm-4.7-flash:latest
- qwen3-coder:30b
```

**Tier 2 (Mid-range - Balanced)**
```
- dolphin-mixtral:8x7b
- devstral-small-2:24b
- qwen2.5:14b-instruct-q4_K_M
- ministral-3:14b
- qwen2.5-128k:latest
```

**Tier 3 (Fast - Speed Optimized)**
```
- ministral-3:latest
- mistral:latest
- qwen2.5:7b-instruct-q5_K_M
- qwen2.5:7b-instruct
```

**Tier 4 (Tiny - Ultra Fast, Mobile)**
```
- llama3.2:latest
- llama3.2-ctx:latest
- lfm2.5-thinking:1.2b
- granite4:1b
```

### 🛠️ Specialized Models

- **Coding:** `qwen3-coder:30b`
- **Long Context:** `qwen2.5-128k:latest` (128K token window)
- **Flagship:** `llama3.3:70b`

**Integration Opportunity:** 
- [ ] Load tier configurations into `model_router.py` for dynamic selection
- [ ] Add `/lm_select` command to choose specific tier
- [ ] Create model family groupings in config

---

## MCP Server Infrastructure

### 🖇️ Native MCP Servers (8+ Registered)

| Server | Purpose | Status | Auth Required |
|--------|---------|--------|----------------|
| **filesystem** | Read/write files | ✅ Ready | Sandbox path |
| **memory** | Knowledge graph | ✅ Ready | N/A |
| **sqlite** | Database operations | ✅ Ready | DB path |
| **brave-search** | Web search | ⚠️ Key Required | `BRAVE_API_KEY` |
| **context7** | Library documentation | ⚠️ Optional | N/A |
| **playwright** | Browser automation | ✅ Ready | N/A |
| **n8n** | Workflow automation | ⚠️ URL + Key | `N8N_URL`, `N8N_API_KEY` |
| **podman** | Container management | ✅ Ready | N/A |
| **github** | GitHub API access | ⚠️ Token Required | `GITHUB_TOKEN` |

### 📋 MCP Tools by Server

#### Filesystem Server
- `read_file` - Read file contents
- `write_file` - Write to file
- `list_directory` - List files
- `search_files` - Pattern matching
- `file_info` - Metadata

#### Memory Server (Knowledge Graph)
- `create_entities` - Add entities
- `create_relations` - Link entities
- `add_observations` - Add facts
- `search_nodes` - Query graph
- `get_entity` - Retrieve entity

#### SQLite Server
- `query` - SELECT queries
- `execute` - Run SQL
- `list_tables` - Show schema
- `describe_table` - Column info
- `insert` - Add data

#### Brave Search
- `web_search` - Search web
- `news_search` - Search news

#### Playwright Server
- `navigate` - Go to URL
- `click` - Click element
- `fill` - Fill form
- `get_text` - Extract text
- `screenshot` - Capture page
- `wait_for` - Wait for element
- `evaluate` - Run JavaScript

#### GitHub Tools (REST API)
- `get_user` - User info
- `list_repos` - List repositories
- `list_issues` - Issues & PRs
- `get_file_contents` - Read file from repo
- `search_code` - Code search
- `create_issue` - New issue
- `create_pull_request` - New PR

#### n8n Server
- `health_check` - Server status
- `list_workflows` - Automation workflows
- `execute_workflow` - Run automation
- `trigger_webhook` - Webhook trigger

#### Podman/Docker
- `list_containers` - Show containers
- `run_container` - New container
- `stop_container` - Stop container
- `container_logs` - View logs
- `pull_image` - Get image

**Integration Opportunity:**
- [ ] Load MCP catalog from JSON registry
- [ ] Add `mcp_enable <server>` skill
- [ ] Create MCP tool router in `agent_tools.py`
- [ ] Build `/skill mcp_*` commands for agent

---

## RAG System Configuration

### 🧠 Production RAG Settings

```json
{
  "backend": "chroma",
  "chroma_path": "./chroma_db",
  "embedding_model": "nomic-embed-text:latest",
  "chunk_size": 800,
  "chunk_overlap": 250,
  "reranker_model": "BAAI/bge-reranker-v2-m3",
  "reranker_device": "cuda:0"
}
```

### 🔍 Search Configuration
- **Search K:** 5 (retrieve top 5 chunks)
- **Rerank Final K:** 3 (rerank top 3 results)
- **Max Context Tokens:** Configurable per query
- **Embedding:** `nomic-embed-text` (768-dim vectors)
- **Reranker:** BAAI BGE Reranker v2-m3 (on GPU)

### 📊 Collections
- Default collection for general knowledge
- Code collection (for `code_chunk_size`: typically 500)
- Separate indexing for different file types

**Status:** ✅ Production RAG already integrated in `production_rag.py`

**Unused Features:**
- [ ] Semantic search vs hybrid search toggle
- [ ] Custom reranking weights
- [ ] Collection-specific search strategies
- [ ] Time-aware retrieval (timestamp filters)

---

## Telegram Bot Features

### 🤖 Not Currently Exposed

#### Message Formatting
- **Gradient text colorization** - `Colors.gradient()` method
- **Animated spinners** during long operations
  - Styles: DOTS, ARROWS, PULSE, FRAMES
- **Rich status messages** with emojis and formatting

#### Command Support
From `telegram_botOG.py`, these commands exist but may need update:
- `/profile` - Hardware profile switching
- `/skill` - Agent persona switching
- `/sandbox` - Safe file editing workflow
- `/tokens` - Token counting utility
- `/youtube` - Video transcript/summarization
- `/ragconfig` - Detailed RAG settings display
- Network security commands (new in OG):
  - `/ports`, `/listeners`, `/inbound`
  - `/netscan`, `/threats`
  - `/devices`, `/newdevices`, `/devicelog`
  - `/approve`, `/block`

#### Conversation Context Tracking
- `ConversationContext` dataclass with:
  - `current_profile` - Hardware mode
  - `current_skill` - Agent persona
  - `debug_mode` - RAG verification output
  - `max_history` - Conversation memory

**Integration Opportunity:**
- [ ] Test and verify all OG commands work with current code
- [ ] Update formatting/spinner styles
- [ ] Add SkillManager integration to telegram_bot.py
- [ ] Verify network security API integration

---

## Security & Network Tools

### 🛡️ Not Yet Integrated

From `telegram_botOG.py` network monitoring:

#### Port Monitoring
```
- Open port detection with risk levels (critical/high/medium/low)
- Listening services enumeration
- Process-to-port mapping
```

#### Connection Tracking
```
- Inbound connection monitoring
- Remote IP identification
- Service associations
```

#### Threat Detection
```
- Keylogger indicators
- Malware signatures
- RAT (Remote Access Trojan) detection
- DDoS attack patterns
- Unfamiliar IP tracking
```

#### Device Tracking
```
- Network device scanning (ARP-based)
- New device detection
- Device approval/blocklist management
- Activity logging per device
- MAC address tracking
```

**Current Status:** Mentioned in telegram bot but requires `self.agent.toolkit.network_monitor` backend

**Integration Opportunity:**
- [ ] Implement `NetworkMonitor` class with above capabilities
- [ ] Add to `agent_tools.py` or separate module
- [ ] Wire up network commands in telegram_bot.py
- [ ] Create device approval workflow

---

## Dependencies (Extended)

### 🔐 From `requirements-linux.txt` (Not in current `requirements.txt`)

#### Financial & Trading
```
ccxt>=4.3.0              # Cryptocurrency exchanges
web3>=6.15.0             # Blockchain/Web3
pandas-ta>=0.3.14b0      # Technical analysis
# ta-lib>=0.4.28          # Advanced indicators (requires compilation)
```

#### Machine Learning (Extended)
```
scikit-learn>=1.4.2      # ML algorithms
xgboost>=2.1.0           # Gradient boosting
lightgbm>=4.5.0          # LightGBM
onnxruntime>=1.17.0      # ONNX model inference
joblib>=1.4.2            # Pipeline serialization
numba>=0.60.0            # JIT compilation
Cython>=3.0.10           # C extensions
```

#### Data Science
```
scipy>=1.13.0            # Scientific computing
openpyxl>=3.1.2          # Excel workbooks
```

#### Distributed Computing
```
uvloop>=0.19.0           # Fast event loop
redis>=5.0.4             # Caching/queues
sqlalchemy>=2.0.30       # ORM
```

#### Observability & Tracing
```
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-exporter-otlp>=1.21.0
opentelemetry-instrumentation>=0.42b0
opentelemetry-instrumentation-requests>=0.42b0
opentelemetry-instrumentation-urllib3>=0.42b0
opentelemetry-instrumentation-sqlite3>=0.42b0
opentelemetry-instrumentation-logging>=0.42b0
```

#### Performance & Encoding
```
msgpack>=1.0.8           # Binary serialization
zstandard>=0.22.0        # Compression
```

#### Testing & Quality
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pylint>=3.0.0
```

#### Visualization
```
matplotlib>=3.9.0        # Plotting
plotly>=5.22.0           # Interactive plots
```

#### Network (Optional - Commented)
```
# scapy>=2.5.0            # Network scanning (Linux)
# paramiko>=3.0.0         # SSH connections
```

### 🚀 Integration Decision

**Current `requirements.txt` has:** 48 packages  
**Extended `requirements-linux.txt` has:** ~120 packages

**Recommendation:**
- [ ] Merge requirements-linux.txt into requirements.txt for feature parity
- [ ] Install: `pip install -r requirements-linux.txt`
- [ ] This enables: trading tools, advanced ML, observability, network scanning

---

## Trading & Finance Tools

### 💱 Not Currently Integrated

#### CCXT (Cryptocurrency Exchange Trading)
```python
# Multi-exchange support: Binance, Kraken, Coinbase, etc.
# Features: market data, order placement, portfolio tracking
# Skills opportunity: /trade <exchange> <symbol>
```

#### Web3 / Blockchain
```python
# Ethereum/Web3 interaction capability
# DeFi protocol interaction
# Smart contract queries
```

#### Technical Analysis (TA)
```python
# pandas-ta: 150+ indicators
# Moving averages, RSI, MACD, Bollinger bands, etc.
# Integration: `/ta <symbol> <timeframe>`
```

#### MT5 / FXJEFE Bridges
From file list (not in code):
- `FXJEFE_EA_Bridge_Patch.mq5` - MT5 Expert Advisor
- `Predict_ZeroMQ.mq5` - ZeroMQ trading bridge
- `Predict.mq5` - MT5 predictor strategy
- `fxjefe_server.py` - Python side of bridge

**Status:** Separate trading system, not fully integrated

---

## Feature Flags

### 🚩 From `larry_config.json`

```json
{
  "features": {
    "voice_enabled": false,
    "mcp_enabled": true,
    "rag_enabled": true,
    "telegram_enabled": true,
    "web_ui_enabled": false
  }
}
```

**Disabled Features:**
- [ ] `voice_enabled` - STT/TTS integration (exists separately)
- [ ] `web_ui_enabled` - Web interface (dashboard_hub.py exists but not integrated)

**Opportunity:**
- [ ] Make these runtime-configurable via skill
- [ ] Add `/feature enable/disable <name>` command
- [ ] Store feature prefs in config

---

## Integration Opportunities

### 📌 High Priority (Phase 3-4)

| Task | Benefit | Effort | Owner |
|------|---------|--------|-------|
| Load model profiles into agent | Dynamic model selection per task | ⭐ Easy | agent_v2.py |
| Integrate MCP catalog | Extensible tool system | ⭐⭐ Medium | agent_tools.py |
| ProfileManager integration | Hardware optimization | ⭐ Easy | agent_v2.py |
| Merge requirements.txt | Enable trading/ML/observability | ⭐ Easy | pip |

### 🔧 Medium Priority (Phase 5+)

| Task | Benefit | Effort |
|------|---------|--------|
| Network security tools | Threat detection + device tracking | ⭐⭐⭐ Hard |
| Telegram feature update | Better bot UX | ⭐⭐ Medium |
| Trading tool integration | CCXT/Web3 support | ⭐⭐⭐ Hard |
| Observability stack | OpenTelemetry tracing | ⭐⭐ Medium |

### 🎯 Low Priority (Future)

| Task | Benefit | Effort |
|------|---------|--------|
| MT5 bridge activation | Full trading system | ⭐⭐⭐⭐ Very Hard |
| Web UI reactivation | Dashboard monitoring | ⭐⭐ Medium |
| Blockchain integration | Web3 capabilities | ⭐⭐⭐ Hard |

---

## Unused Files from Compressedall

### 📄 Files Not in Current Workspace

```
FULL SYNC ACHIEVED All.txt         - Status log
FULL SYNC COMPLETE Every.txt       - Status log
Feature alignment report.html      - Report
FXJEFE_EA_Bridge_Patch.mq5        - MT5 EA
Predict_ZeroMQ.mq5                - ZeroMQ bridge
Predict.mq5                        - MT5 strategy
looting_larry_scanner.ps1         - PowerShell security tool
looting_larry_ultimate.sh          - Bash security scanning
looting_larry_ultimate1.sh         - Alt version
homelab_security_scan.sh           - Homelab scanner
autonomous_security_toolkit.py     - Security automation
kali_tools.py                      - Kali Linux tools
network_hunter_tools.py            - Network recon
port_investigator.py               - Port scanning
BASH_INTEGRATION_PATCHES.py        - Bash integration
```

---

## Summary

### ✅ What's Already Integrated
- GPU-optimized hardware configuration
- Ollama model routing
- RAG system with reranking
- MCP client infrastructure
- Web tools and YouTube support
- Telegram bot base

### 📚 What's Available but Unused
- Model profile tiers (Tier 1-4)
- Extended MCP server catalog (8+ servers)
- Advanced RAG configuration
- Network security commands
- Device tracking system
- Trading tool infrastructure (CCXT, Web3)
- Extended dependencies (120+ packages)
- Specialized models (coding, context-extended)

### 🚀 Next Steps
1. **Load model profiles** into configuration system
2. **Build MCP registry** in JSON format
3. **Expose network tools** via skills
4. **Test trading libs** if needed
5. **Document integration points** for each feature

---

**Last Updated:** 2026-04-13  
**Next Review:** After Phase 3 (Config Management) completion  
**Maintainer:** Larry G-FORCE System
