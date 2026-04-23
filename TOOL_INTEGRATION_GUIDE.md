# 🔗 Tool Ecosystem Integration Guide
**Agent-Larry v2.1 | Multi-Suite Tool Architecture**

---

## 📊 Tool Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT-LARRY TOOL ECOSYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │  agent_v2.py     │  │  agent_tools.py  │                   │
│  │  SkillManager    │  │  Process Mgmt    │                   │
│  │  (8 skills)      │  │  Job Scheduling  │                   │
│  └────────┬─────────┘  │  Health Checks   │                   │
│           │            │  Remote Execution│                   │
│           │            └────────┬─────────┘                   │
│           │                     │                               │
│  ┌────────v──────────────────────v─────────────────┐          │
│  │            TaskOrchestrator                     │          │
│  │   (Input Validation → Execution → Verification) │          │
│  └────────┬──────────────────────────┬──────────────┘          │
│           │                          │                         │
│  ┌────────v────────────┐  ┌─────────v────────────┐           │
│  │  web_tools.py       │  │  kali_tools.py      │           │
│  │  Web Scraping ────► │  │  Security Recon     │           │
│  │  URL Fetch      MD  │  │  Port Scanning      │           │
│  │  HTML→Markdown      │  │  DNS Enumeration    │           │
│  │  YouTube Trans.     │  │  Vulnerability Scan │           │
│  │  Ollama Summary     │  │  Password Testing   │           │
│  └─────────────────────┘  └─────────────────────┘           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  OUTPUT LAYER: Standardized Format                      │   │
│  │  ├─ ToolResult (individual tool execution)             │   │
│  │  ├─ TaskResult (aggregated results)                    │   │
│  │  └─ JSON/JSON output for external systems              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Tool Categories & Functions

### 1. agent_v2.py (SkillManager - 8 skills)

#### System Skills (3)
| Name | Function | Output |
|------|----------|--------|
| `system_health` | CPU/Memory/Disk metrics | JSON-formatted dashboard |
| `agent_uptime` | Runtime duration | Human-readable "Xh Ym Zs" |
| `skill_stats` | Skill breakdown by category | Statistics table |

#### Telegram Skills (2)
| Name | Function | Requirements |
|------|----------|--------------|
| `telegram_bot_status` | Check bot token validity | TELEGRAM_BOT_TOKEN |
| `telegram_send_test` | Send test message | TELEGRAM_BOT_TOKEN + CHAT_ID |

#### File System Skills (1)
| Name | Function | Returns |
|------|----------|---------|
| `list_files` | Directory listing | File count + preview |

#### Maintenance Skills (1)
| Name | Function | Output |
|------|----------|--------|
| `quick_backup` | Agent file backup | Backup file path |

#### Meta Skills (1)
| Name | Function | Returns |
|------|----------|---------|
| `hello_world` | Test skill | "Hello from Agent-Larry!" |

---

### 2. agent_tools.py (Process Management)

#### Core Functions
```python
# Execute scripts synchronously
run_script(path, args, cwd, timeout, host)
→ {"ok": bool, "exit_code": int, "stdout": str, "stderr": str}

# Launch background jobs
start_background(path, name, args, host)
→ {"ok": bool, "pid": int, "log": str}

# Kill background jobs
stop_background(name, host)
→ {"ok": bool, "killed": int}

# List all jobs
list_jobs(host)
→ {"ok": bool, "jobs": {name → {pid, path, alive}}}

# Health checks (URL or script)
health_check(target, host)
→ {"ok": bool, "status": int, "body": str}

# Schedule recurring checks
schedule_interval(target, interval_seconds, name, host)
→ {"ok": bool, "next_run": str}
```

#### Features
- ✅ Secure path allow-listing
- ✅ Remote execution via Windows Meshnet
- ✅ APScheduler integration
- ✅ Telegram failure alerts (deduplicated)
- ✅ Job state persistence (~/.robin/jobs.json)

---

### 3. web_tools.py (Web Operations)

#### WebScraper Class
```python
# Fetch and convert web pages
fetch_url(url, timeout=30)
→ (content, success)

html_to_markdown(html, url="")
→ markdown_string

scrape_and_save(url)
→ (filepath, success)

summarize_url(url, model, ollama_url, focus)
→ summary_string
```

#### YouTubeSummarizer Class
```python
# Extract video transcripts
extract_transcript(video_id, language="en")
→ transcript_dict

# Summarize transcript with Ollama
summarize_content(video_id, model, focus)
→ summary_string

# Store in ChromaDB for RAG
persist_to_chromadb(video_id, content)
→ bool
```

#### Capabilities
- ✅ HTML → Markdown conversion (BeautifulSoup)
- ✅ YouTube transcript extraction
- ✅ Ollama summarization (local LLM)
- ✅ ChromaDB persistence for RAG
- ✅ Browser cookie support (authenticated requests)

---

### 4. kali_tools.py (Security/Recon - 20+ tools)

#### Recon/Network (5 tools)
| Tool | Category | Presets |
|------|----------|---------|
| `nmap` | Port scanning | quick, full, service, vuln, os, stealth, udp |
| `masscan` | Fast async scanning | quick, full, web |
| `arp-scan` | Network discovery | local, iface |
| `dig` | DNS queries | any, mx, txt, axfr |
| `host` | DNS lookups | (direct) |

#### DNS/OSINT (6 tools)
| Tool | Category | Function |
|------|----------|----------|
| `whois` | Domain/IP lookups | Get WHOIS data |
| `dnsenum` | DNS enumeration | Zone enumeration |
| `searchsploit` | Exploit-DB | Search exploits |

#### Web Penetration (7 tools)
| Tool | Example |
|------|---------|
| `nikto` | Web server vuln scanning |
| `whatweb` | Technology fingerprinter |
| `gobuster` | Directory/DNS brute-forcer |
| `dirb` | Directory brute-forcer |
| `wfuzz` | Web fuzzer |
| `sqlmap` | SQL injection scanner |
| `curl` | HTTP requests |

#### SMB/Exploitation (4+ tools)
| Tool | Function |
|------|----------|
| `enum4linux` | SMB enumeration |
| `smbclient` | SMB client |
| `hydra` | Password cracker |

---

## 🔄 Execution Flow Diagram

```
┌─────────────────┐
│  User Request   │
│  (Natural or    │
│   structured)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  TaskRequest Parsing            │
│  ├─ Extract task_id            │
│  ├─ Parse tool list            │
│  ├─ Get parameters             │
│  └─ Set timeout                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  INPUT VALIDATION              │
│  ├─ task_id non-empty?         │
│  ├─ tools non-empty?           │
│  ├─ timeout 10-3600s?          │
│  └─ Return: valid or error     │
└────────┬────────────────────────┘
         │
    ┌────┴─────┐
    ▼          ▼
  ERROR      ✅ VALID
    │          │
    │          ▼
    │    ┌─────────────────────────┐
    │    │  TOOL EXECUTION         │
    │    │  For each tool:         │
    │    │  ├─ Call ToolExecutor   │
    │    │  ├─ Wait for result     │
    │    │  ├─ Capture stdout      │
    │    │  ├─ Catch exceptions    │
    │    │  └─ Record time/status  │
    │    └────────┬────────────────┘
    │             │
    │             ▼
    │    ┌─────────────────────────┐
    │    │  RESULT AGGREGATION     │
    │    │  ├─ Collect all results │
    │    │  ├─ Calculate duration  │
    │    │  ├─ Determine status    │
    │    │  └─ Build TaskResult    │
    │    └────────┬────────────────┘
    │             │
    └─────┬───────┘
          │
          ▼
┌─────────────────────────────────┐
│  OUTPUT GENERATION              │
│  ├─ Format as ToolResult[]      │
│  ├─ Generate summary            │
│  ├─ Calculate statistics        │
│  └─ Create JSON output          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  REPORT & VERIFICATION          │
│  ├─ Verify output format        │
│  ├─ Check all fields present    │
│  ├─ Generate human report       │
│  └─ Save to file                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  DELIVERY                       │
│  ├─ Print formatted report      │
│  ├─ Return JSON structure       │
│  ├─ Save to file                │
│  └─ Log metrics                 │
└─────────────────────────────────┘
```

---

## 🔗 Integration Points

### SkillManager → agent_tools
```python
# Use agent_tools health_check for monitoring
from agent_tools import health_check

# Register as skill
def _skill_monitor_url(url=None, **kwargs):
    if not url:
        return {"success": False, "error": "URL required"}
    result = health_check(url)
    return {
        "success": result.get("ok"),
        "result": f"Status: {result.get('status')}",
        "error": result.get("error")
    }

# Can be called via /skill monitor_url {"url": "http://example.com"}
```

### SkillManager → web_tools
```python
# Register web scraping skill
from web_tools import WebScraper

def _skill_scrape_page(url=None, **kwargs):
    if not url:
        return {"success": False, "error": "URL required"}
    
    scraper = WebScraper()
    result = scraper.scrape(url)
    if result:
        return {"success": True, "result": result[:500]}
    return {"success": False, "error": "Failed to scrape"}

# Can be called via /skill scrape_page {"url": "http://example.com"}
```

### SkillManager → kali_tools
```python
# Register port scan skill (requires tool installed)
from kali_tools import run_kali_tool

def _skill_scan_ports(target=None, **kwargs):
    if not target:
        return {"success": False, "error": "target required"}
    
    result = run_kali_tool("nmap", target, preset="quick")
    return {
        "success": result.get("ok"),
        "result": result.get("output", "")[:1000],
        "error": result.get("error")
    }
```

---

## 📈 Tool Capability Matrix

| Capability | agent_v2 | agent_tools | web_tools | kali_tools |
|-----------|----------|-------------|-----------|-----------|
| Real-time metrics | ✅ | ✅ | — | — |
| Process management | — | ✅ | — | — |
| Job scheduling | — | ✅ | — | — |
| Remote execution | — | ✅ | — | — |
| Telegram alerts | — | ✅ | — | — |
| Web scraping | — | — | ✅ | — |
| URL fetching | — | — | ✅ | — |
| LLM integration | — | — | ✅ | — |
| ChromaDB RAG | — | — | ✅ | — |
| Port scanning | — | — | — | ✅ |
| DNS queries | — | — | — | ✅ |
| Web vulns | — | — | — | ✅ |
| Penetration | — | — | — | ✅ |

---

## 🚀 Usage Examples

### Example 1: System Health Check (Uses agent_v2)
```bash
# Via command line
/skill system_health

# Output
📊 **System Health Dashboard**
CPU: 8.9%
Memory: 18.2% (50GB free)
Disk: 87.9% (211GB free)
Uptime: 750s
```

### Example 2: Schedule Health Monitoring (Uses agent_tools)
```python
from agent_tools import schedule_interval

schedule_interval(
    target="http://localhost:8080",
    interval_seconds=300,
    name="monitor_api"
)

# Checks every 5 minutes, alerts via Telegram on failure
```

### Example 3: Web Content Summary (Uses web_tools)
```python
from web_tools import WebScraper

scraper = WebScraper()
summary = scraper.summarize_url(
    "https://example.com/article",
    focus="prices"
)

# Returns LLM-generated summary focusing on prices
```

### Example 4: Port Scanning (Uses kali_tools)
```python
from kali_tools import run_kali_tool

result = run_kali_tool(
    "nmap",
    "192.168.1.100",
    preset="quick"
)

# Returns: {"ok": bool, "output": str}
```

---

## 🔐 Security Features

### Per-Tool Suite

**agent_v2 (SkillManager)**
- ✅ Parameter validation
- ✅ Error handling & logging
- ✅ No external calls by default

**agent_tools**
- ✅ Secure path allow-listing ($LARRY_ALLOWED_ROOTS)
- ✅ Process isolation (start_new_session)
- ✅ Job state persistence
- ✅ Remote host support via Meshnet
- ✅ Timeout protection on all commands

**web_tools**
- ✅ User-Agent masking to avoid blocks
- ✅ Request timeouts
- ✅ Beautiful HTML parsing (removes scripts/styles)
- ✅ Optional browser cookie support

**kali_tools**
- ✅ Tool availability checking
- ✅ Timeout handling per tool
- ✅ Output sanitization (last 4KB kept)
- ✅ Subprocess isolation

---

## 📊 Performance Profile

| Tool Suite | Avg Response | Max Response | Best For |
|-----------|--------------|--------------|----------|
| agent_v2 (SkillManager) | 100ms-1s | ~ 1s | Quick system checks |
| agent_tools | 5-30s | 300s (configurable) | Background jobs |
| web_tools | 1-5s | 30s (configurable) | Content extraction |
| kali_tools | 10-120s | 300s+ (tool-dependent) | Security scans |

---

## 🎯 Common Task Patterns

### Pattern 1: Health Monitoring
```
SkillManager (system_health)
    ↓
agent_tools (schedule_interval)
    ↓
Telegram Alert (on failure)
```

### Pattern 2: Content Extraction
```
web_tools (scrape_to_markdown)
    ↓
web_tools (summarize_url via Ollama)
    ↓
ChromaDB (persist for RAG)
```

### Pattern 3: Security Assessment
```
kali_tools (nmap scan)
    ↓
kali_tools (nikto web scan)
    ↓
agent_tools (schedule follow-up)
```

### Pattern 4: Multi-Tool Orchestration
```
TaskRequest
    ├─ SkillManager (collect metrics)
    ├─ agent_tools (check health)
    ├─ web_tools (scrape latest info)
    ├─ kali_tools (scan for vulns)
    └─ Aggregated Report
```

---

## ✅ Integration Checklist

- [x] All tools use standardized response format
- [x] Error handling is consistent across suites
- [x] Timeout protection on long-running tools
- [x] Logging integrated (SkillManager uses logger)
- [x] Remote execution capability (agent_tools)
- [x] Circular dependency prevention
- [x] Performance acceptable (< 1s for quick operations)

---

**Version:** 1.0  
**Last Updated:** 2026-04-13  
**Status:** 🟢 **PRODUCTION READY**
