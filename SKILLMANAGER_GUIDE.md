# 🧰 SkillManager API — Production Guide
**Agent-Larry v2.1 | Fully Robust & Production-Ready**

---

## Table of Contents
1. [What is SkillManager?](#what-is-skillmanager)
2. [Core API Methods](#core-api-methods)
3. [Built-in Skills (Enabled by Default)](#built-in-skills-enabled-by-default)
4. [How to Add Custom Skills](#how-to-add-custom-skills)
5. [SkillManager vs LangChain](#skillmanager-vs-langchain)
6. [Production Best Practices](#production-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## What is SkillManager?

**SkillManager** is a lightweight, zero-dependency registry that lets your agent register and execute reusable skills (small, self-contained functions with metadata).

### Why SkillManager?
- ✅ **Light**: No external dependencies (psutil optional)
- ✅ **Fast**: Direct Python function calls, no serialization overhead
- ✅ **Secure**: Local-first, no external API calls unless you initiate them
- ✅ **Debuggable**: Easy to trace, hot-reload friendly
- ✅ **LLM-Friendly**: Provides structured metadata that prevents hallucination

---

## Core API Methods

### 1. `register_skill(name, func, description, category)`
Register a new skill at startup or runtime.

```python
self.skill_manager.register_skill(
    name="telegram_bot_status",           # Unique identifier (lowercase + underscore)
    func=self._skill_telegram_status,      # Python function (must accept **kwargs)
    description="Check if your Telegram bot token is valid and online",
    category="telegram"                    # For grouping (system, telegram, file, etc.)
)
```

**Parameters:**
- `name` (str): Unique skill identifier, used in `/skill <name>` commands
- `func` (callable): Function that accepts optional `params` dict and returns a dict with `{"success": bool, "result": str, "error": str}`
- `description` (str): One-line description shown in skill listings
- `category` (str): Grouping category ("telegram", "system", "filesystem", etc.)

---

### 2. `execute_skill(name, params=None)`
Run a skill by name with optional parameters.

```python
result = agent.skill_manager.execute_skill("telegram_bot_status")
if result.get("success"):
    print(f"✅ {result['result']}")
else:
    print(f"❌ {result.get('error', 'Unknown error')}")
```

**Returns:**
```json
{
  "success": true,
  "result": "✅ Telegram bot is ONLINE!\nName: LarryBot\nUsername: @larrybot\nID: 123456789"
}
```

---

### 3. `get_all_skills()`
Get all registered skills grouped by category. **This is what the LLM calls to discover available skills.**

```python
skills_data = agent.skill_manager.get_all_skills()
# Returns:
# {
#   "telegram": [
#     {"name": "telegram_bot_status", "description": "Check bot health", "category": "telegram"},
#     {"name": "telegram_send_test", "description": "Send test message", "category": "telegram"}
#   ],
#   "system": [...],
#   ...
# }
```

---

### 4. `get_skill_count()`
Get total number of registered skills.

```python
count = agent.skill_manager.get_skill_count()
print(f"Total skills: {count}")  # Total skills: 7
```

---

## Built-in Skills (Enabled by Default)

### 1. **telegram_bot_status** (`telegram`)
Check if your Telegram bot token is valid and online.

```bash
/skill telegram_bot_status
```

**Output (with token set):**
```
✅ Telegram bot is ONLINE!
Name: LarryBot
Username: @larrybot
ID: 123456789
```

**Setup:**
```bash
export TELEGRAM_BOT_TOKEN="123:ABC..."
```

---

### 2. **telegram_send_test** (`telegram`)
Send a test message to yourself via Telegram bot.

```bash
/skill telegram_send_test
```

**Setup (required):**
```bash
export TELEGRAM_BOT_TOKEN="123:ABC..."
export TELEGRAM_CHAT_ID="987654321"
```

**Output:**
```
✅ Test message sent to Telegram!
```

---

### 3. **system_health** (`system`)
Full system + agent health dashboard (CPU, Memory, Disk, Uptime).

```bash
/skill system_health
```

**Output:**
```
📊 **System Health Dashboard**
CPU: 45.2%
Memory: 62% (8GB free)
Disk: 71% (200GB free)
Uptime: 3600s
Timestamp: 2026-04-13 14:30:45
```

**Requires:** `psutil` (installed via `pip install psutil`)

---

### 4. **quick_backup** (`system`)
Create instant backup of the main agent file.

```bash
/skill quick_backup
```

**Output:**
```
✅ agent_v2.py backed up to /path/to/backups
```

**Creates:** `backups/agent_v2.py.bak-20260413-143045`

---

### 5. **skill_stats** (`system`)
Show execution statistics for all skills (breakdown by category).

```bash
/skill skill_stats
```

**Output:**
```
📈 **Skill Statistics**
Total registered: 7

• Telegram: 2
• System: 3
• Filesystem: 1
• Meta: 1
```

---

### 6. **agent_uptime** (`system`)
Display how long the agent has been running in human-readable format.

```bash
/skill agent_uptime
```

**Output:**
```
⏱️ Agent uptime: 1h 23m 45s
```

---

### 7. **list_files** (`filesystem`)
List files in a directory (default: current directory).

```bash
/skill list_files
/skill list_files {"path": "/home/user/Documents"}
```

**Output:**
```
📁 Files in .:
agent_v2.py
SKILLMANAGER_GUIDE.md
requirements.txt
backups/
... and 23 more files
```

---

## How to Add Custom Skills

### Template: Copy-Paste for New Skills

```python
# Inside _register_agent_skills() method:

def _skill_your_new_skill(**kwargs):
    """Docstring becomes the description."""
    try:
        # Your logic here
        result = "Success message or result"
        logger.info("your_new_skill executed successfully")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"your_new_skill failed: {e}")
        return {"success": False, "error": str(e)}

self.skill_manager.register_skill(
    name="your_new_skill",
    func=_skill_your_new_skill,
    description="One-line description shown in /skill list",
    category="your_category"  # or "telegram", "system", "file", etc.
)
```

---

### Example 1: Add Advanced Telegram Skill

```python
def _skill_telegram_get_updates(**kwargs):
    """Fetch latest Telegram messages."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    try:
        import requests
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        data = r.json()
        if data["ok"]:
            updates = data.get("result", [])
            if not updates:
                return {"success": True, "result": "✅ No new messages"}
            msg_count = len(updates)
            latest = updates[-1].get("message", {}).get("text", "—")
            return {
                "success": True,
                "result": f"📨 {msg_count} update(s)\\nLatest: {latest}"
            }
        return {"success": False, "error": "Telegram API error"}
    except Exception as e:
        return {"success": False, "error": str(e)}

self.skill_manager.register_skill(
    name="telegram_get_updates",
    func=_skill_telegram_get_updates,
    description="Fetch latest Telegram messages from your bot",
    category="telegram"
)
```

**Usage:**
```bash
/skill telegram_get_updates
```

---

### Example 2: Add File System Skill

```python
def _skill_find_large_files(**kwargs):
    """Find files larger than 100MB."""
    try:
        import os
        large_files = []
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            for f in files:
                try:
                    path = os.path.join(root, f)
                    if os.path.getsize(path) > 100 * 1024 * 1024:  # 100MB
                        large_files.append((path, os.path.getsize(path) // (1024**2)))
                except:
                    pass
            if len(large_files) > 20:
                break  # Stop after finding 20
        
        if not large_files:
            return {"success": True, "result": "✅ No files >100MB found"}
        
        result = "📦 Large files (>100MB):\\n"
        for path, size_mb in large_files[:10]:
            result += f"• {path} ({size_mb}MB)\\n"
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

self.skill_manager.register_skill(
    name="find_large_files",
    func=_skill_find_large_files,
    description="Find files larger than 100MB on your system",
    category="filesystem"
)
```

---

## SkillManager vs LangChain

| Feature | Your SkillManager | LangChain Tools |
|---------|-------------------|-----------------|
| **Dependencies** | Zero (psutil optional) | Heavy (pydantic, langchain-core, etc.) |
| **Registration** | One-line `register_skill()` | Boilerplate + decorators |
| **Execution** | Plain Python functions | Complex StructuredTool + chains |
| **Discoverability** | Built-in categories + examples | Needs JSON schema parsing |
| **Token Usage** | Minimal (concise descriptions) | High (verbose JSON schemas) |
| **Debugging** | Easy, plain Python | Complex async/chain tracing |
| **Best For** | Local autonomous agents | Cloud-scale multi-agent systems |
| **Security** | Local-first, full control | More complex attack surface |

### Recommendation
✅ **Stick with SkillManager** — it's lighter, faster, safer, and perfectly matched to your local G-FORCE agent.

---

## Production Best Practices

### 1. Error Handling & Logging
Always wrap skill logic in try-except and return standardized dicts:

```python
def _skill_example(**kwargs):
    try:
        # Your logic
        result = do_something()
        logger.info("skill_example: completed")
        return {"success": True, "result": result}
    except TimeoutError as e:
        logger.error(f"skill_example: timeout {e}")
        return {"success": False, "error": f"Timeout: {e}"}
    except Exception as e:
        logger.error(f"skill_example: failed {e}")
        return {"success": False, "error": str(e)}
```

### 2. Timeout Protection
For long-running skills, use `timeout` or `threading.Timer`:

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Skill execution timeout")

def _skill_long_running(**kwargs):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30-second timeout
    try:
        result = run_long_task()
        signal.alarm(0)  # Cancel alarm
        return {"success": True, "result": result}
    except TimeoutError:
        return {"success": False, "error": "Execution timeout (30s limit)"}
```

### 3. Parameter Validation
Validate skill parameters before use:

```python
def _skill_with_params(path=None, **kwargs):
    if not path:
        return {"success": False, "error": "Missing required parameter: path"}
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}
    # Your logic
    return {"success": True, "result": "Done"}
```

### 4. Secure Environment Variables
Always fetch secrets from environment, never hardcode:

```python
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN not set in environment")
```

### 5. Category Naming Convention
Use consistent, lowercase categories:
- `system` — System info, health, uptime
- `telegram` — Telegram bot integration
- `filesystem` — File/directory operations
- `network` — HTTP, DNS, connectivity
- `analytics` — Data analysis, stats
- `maintenance` — Backups, cleanup

---

## Troubleshooting

### "Skill not found" Error
```
❌ Skill 'xyz' not found
```

**Fix:** Check skill name in `/skill list`. Skill names are case-sensitive and use underscores.

```bash
# List all skills first
list all current agent skills

# Then use exact name
/skill telegram_bot_status  # ✅ Correct
/skill TelegramBotStatus    # ❌ Wrong (case matters)
```

---

### "TELEGRAM_BOT_TOKEN not set"
```
ℹ️ No TELEGRAM_BOT_TOKEN in environment.
Add it to .env for full Telegram support.
```

**Fix:**
```bash
# Add to ~/.bashrc or .env file
export TELEGRAM_BOT_TOKEN="123:ABC..."
export TELEGRAM_CHAT_ID="987654321"

# Reload shell
source ~/.bashrc
```

---

### Skill Execution Timeout
```
❌ Skill failed: Execution timeout
```

**Fix:** Skill took too long. Either:
1. Optimize the skill function
2. Increase timeout in `execute_skill()` if available
3. Break the skill into smaller sub-skills

---

### psutil Import Error
```
❌ system_health failed: No module named 'psutil'
```

**Fix:**
```bash
pip install psutil
```

---

### Skills Not Showing in List
```python
# Make sure skill is registered in _register_agent_skills():
self.skill_manager.register_skill(...)
```

Check logs during startup:
```bash
python agent_v2.py 2>&1 | grep "Registered skill"
```

You should see:
```
✅ SkillManager initialized
Registered skill: telegram_bot_status → telegram
Registered skill: telegram_send_test → telegram
...
✅ All 7 skills registered
```

---

## Summary

| Task | Command |
|------|---------|
| List all skills | `list all current agent skills` or `/skill` |
| Run a skill | `/skill <name>` |
| Add custom skill | Edit `_register_agent_skills()` (see template above) |
| Check Telegram | `/skill telegram_bot_status` |
| System health | `/skill system_health` |
| Backup agent | `/skill quick_backup` |
| View skill stats | `/skill skill_stats` |

---

**Version:** Agent-Larry v2.1 (2026-04-13)  
**Status:** Production-Ready ✅  
**Last Updated:** 2026-04-13 14:30 UTC
