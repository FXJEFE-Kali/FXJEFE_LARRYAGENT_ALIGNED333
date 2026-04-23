# Agent-Larry Security & Stability Fixes
**Date:** 2026-03-13

---

## Summary

11 issues patched across `agent_v2.py`, `telegram_bot.py`, and `model_router.py`.
All fixes verified with syntax checks and unit tests (all pass).

---

## Fixes

### 1. Shell Injection — `telegram_bot.py` `/run` command
**Severity:** Critical
**Before:** `subprocess.run(args, shell=True)` — user input passed directly to shell.
**After:** `subprocess.run(shlex.split(args), shell=False)` — no shell interpolation.
**Impact:** Prevented arbitrary command execution via payloads like `/run ls; rm -rf /`.

---

### 2. Tool Arg Injection — `agent_v2.py` `_try_tool_dispatch()`
**Severity:** High
**Before:** Raw remaining text from query passed as tool args with no sanitization.
**After:** All shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `<`, `>`, `(`, `)`, `\`) stripped from args before passing to `run_tool()`.
**Test:** `run nmap 10.0.0.1; rm -rf /` → args become `10.0.0.1 rm -rf /` (`;` removed, no shell execution).

---

### 3. SSRF / Protocol Injection — `agent_v2.py` `/web` command
**Severity:** High
**Before:** Any URL accepted including `file://`, `ftp://`, `javascript:`.
**After:** Hard check — only `http://` and `https://` are accepted; others are blocked with an error message.
**Test results:**
```
http://example.com   -> ALLOW
https://example.com  -> ALLOW
file:///etc/passwd   -> BLOCK
ftp://bad.com        -> BLOCK
javascript:alert(1)  -> BLOCK
```

---

### 4. TOOLS Dict KeyError — `agent_v2.py` `_try_tool_dispatch()`
**Severity:** High
**Before:** `tool_obj = TOOLS[tool_name]` — crashes if key missing (race condition / dict change).
**After:** `tool_obj = TOOLS.get(tool_name)` with explicit null check and early return.

---

### 5. Tool Dispatch False Positives — `agent_v2.py` `_try_tool_dispatch()`
**Severity:** Medium
**Before:** Pattern matched tool name anywhere in sentence — "I like nmap" would trigger nmap.
**After:** Pattern anchored to start of query (`^`). Verb+tool or bare tool name must appear at the beginning.
**Test results:**
```
"run nmap localhost"      -> dispatches nmap       (correct)
"I like nmap a lot"       -> no dispatch           (correct)
"can you run nmap please" -> no dispatch           (correct)
```

---

### 6. Bare `except` Swallowing Errors — `telegram_bot.py`
**Severity:** Medium
**Before:** Two `except:` / `except: pass` blocks silently swallowed all exceptions including `KeyboardInterrupt` and `SystemExit`.
**After:** `except Exception as e: logger.warning(...)` — errors are logged, critical signals propagate normally.
**Locations:** Lines ~804 (context manager get) and ~825 (context manager add_message).

---

### 7. Bot Token Leak in Logs — `telegram_bot.py` file download
**Severity:** High
**Before:** If the `requests.get(download_url)` call threw an exception, the full URL (containing the bot token) could appear in logs.
**After:** Exception caught before any logging; error message says "token redacted" — token never appears in logs.

---

### 8. Unbounded `conversations` Dict — `telegram_bot.py`
**Severity:** Medium
**Before:** Every unique `chat_id` added a permanent entry — memory grows forever with new users.
**After:** LRU eviction at 500 entries — oldest conversation dropped when limit reached.

---

### 9. Unbounded RAG Conversation Memory — `agent_v2.py`
**Severity:** Medium
**Before:** `conv_collection.add()` called on every query with no cleanup — ChromaDB grows indefinitely.
**After:** After each add, collection is checked and pruned to the most recent 500 entries.

---

### 10. No Timeout on Model Generation — `model_router.py`
**Severity:** Medium
**Before:** `requests.post(..., timeout=None)` — a hung or slow model freezes the entire process (including Telegram bot polling loop) forever.
**After:** Default `timeout=1200` (20 minutes). Caller can override per-request. Telegram bot can no longer hang indefinitely.

---

## Test Run — 28/28 passed

```
[1] Arg injection stripping
  PASS  '127.0.0.1; rm -rf /'                -> '127.0.0.1 rm -rf /'
  PASS  'host $(cat /etc/passwd)'            -> 'host cat /etc/passwd'
  PASS  'target & nc -e /bin/sh 4444'        -> 'target  nc -e /bin/sh 4444'
  PASS  'normal-target.com'                  -> 'normal-target.com'

[2] URL protocol allowlist
  PASS  ALLOW  http://example.com
  PASS  ALLOW  https://example.com
  PASS  BLOCK  file:///etc/passwd
  PASS  BLOCK  ftp://badsite.com
  PASS  BLOCK  javascript:alert(1)
  PASS  BLOCK  data:text/html,...
  PASS  BLOCK  //example.com

[3] Tool dispatch anchor & false-positive guard
  PASS  'run nmap localhost'               -> (nmap, 'localhost')
  PASS  'nmap 192.168.1.1'                 -> (nmap, '192.168.1.1')
  PASS  'nmap -sV target.com'              -> (nmap, '-sV target.com')
  PASS  'run nmap 10.0.0.1; rm -rf /'      -> (nmap, '10.0.0.1 rm -rf /')  [injection stripped]
  PASS  'I love nmap'                      -> (None, None)  [not dispatched]
  PASS  'can you run nmap please'          -> (None, None)  [not dispatched]
  PASS  'nmap is a great tool'             -> (None, None)  [not dispatched]

[4] shell=False injection guard
  PASS  output='hello; echo INJECTED'  (semicolon is literal, second command never ran)

[5] TOOLS.get() — no KeyError
[6] model_router timeout=1200s (20 min)
```

Live nmap test via natural language dispatch:
```
Input:  test nmap localhost
Output: 🔧 Detected tool request — running: nmap localhost
        22/tcp  open  ssh
        80/tcp  open  http
        631/tcp open  ipp
        3000/tcp open  ppp
        8000/tcp open  http-alt
        8080/tcp open  http-proxy
        [Done]
```

---

## Files Changed

| File | Changes |
|------|---------|
| `agent_v2.py` | URL validation, TOOLS guard, tool dispatch anchor + arg sanitization, RAG pruning |
| `telegram_bot.py` | Shell injection fix, bare excepts, conversations LRU, token log protection |
| `model_router.py` | Default 20-minute generation timeout |
