#!/usr/bin/env python3
"""
Local Larry v2 — G-FORCE Enhanced Agent
- Multi-model support with task-based routing
- Context limits per model
- File browsing and editing
- Persistent ChromaDB RAG
- Hardware profiles (SPEED / ACCURACY / ULTRA_CONTEXT)
- Sandbox safe-edit workflow
- Voice, MCP tools, web scraping
- Autonomous agentic mode
- 100% localhost (no external APIs)
"""

import asyncio
import os
import sys
import re
import platform
import hashlib
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import subprocess
import json
import logging
import tempfile
import shutil
import uuid

# pandas is optional — only required for /csv-edit
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# Fix Windows console encoding for Unicode/emoji support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

try:
    import readline
except ModuleNotFoundError:
    try:
        import pyreadline3 as readline
    except ModuleNotFoundError:
        readline = None

# Bracketed-paste markers. Terminals wrap pastes in ESC[200~ ... ESC[201~ when
# bracketed paste mode is enabled (ESC[?2004h). We enable it at startup so
# multi-line pastes arrive as one message instead of one-per-line.
BPASTE_START = "\x1b[200~"
BPASTE_END = "\x1b[201~"
_BPASTE_ENABLED = False


def _enable_bracketed_paste():
    global _BPASTE_ENABLED
    if _BPASTE_ENABLED:
        return
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return
    if sys.platform == "win32":
        return
    try:
        sys.stdout.write("\x1b[?2004h")
        sys.stdout.flush()
        _BPASTE_ENABLED = True
    except Exception:
        pass


def _disable_bracketed_paste():
    global _BPASTE_ENABLED
    if not _BPASTE_ENABLED:
        return
    try:
        sys.stdout.write("\x1b[?2004l")
        sys.stdout.flush()
    except Exception:
        pass
    _BPASTE_ENABLED = False


def read_user_input(prompt):
    """input() wrapper that auto-joins bracketed pastes into a single string.

    If readline already coalesces the paste (GNU readline 8+), this is a no-op.
    Otherwise we see ESC[200~ at the start of a line, buffer subsequent lines
    until ESC[201~, and return the joined content.
    """
    raw = input(prompt)

    if BPASTE_START not in raw:
        return raw

    start_idx = raw.index(BPASTE_START) + len(BPASTE_START)
    prefix = raw[:raw.index(BPASTE_START)]
    first = raw[start_idx:]

    # Single-line paste: end marker on same line
    if BPASTE_END in first:
        end_idx = first.index(BPASTE_END)
        return prefix + first[:end_idx] + first[end_idx + len(BPASTE_END):]

    buffered = [first]
    while True:
        try:
            line = input()
        except EOFError:
            break
        if BPASTE_END in line:
            end_idx = line.index(BPASTE_END)
            buffered.append(line[:end_idx])
            tail = line[end_idx + len(BPASTE_END):]
            result = prefix + "\n".join(buffered)
            if tail:
                result += tail
            return result
        buffered.append(line)

    return prefix + "\n".join(buffered)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
    from rich.theme import Theme
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    Console = Panel = Prompt = Text = Theme = box = None
    RICH_AVAILABLE = False

# Import our core modules
from model_router import ModelRouter, TaskType, list_models, get_router, MODEL_CONFIGS
from file_browser import FileBrowser, get_browser
from kali_tools import TOOLS, list_tools, tool_help, run_tool, parse_args_with_preset
from activity_stream import ActivityStream

# Skill Manager
try:
    from skill_manager import get_skill_manager
    SKILL_MANAGER_AVAILABLE = True
except ImportError:
    get_skill_manager = None
    SKILL_MANAGER_AVAILABLE = False

# Context Manager
try:
    from context_manager import ContextManager, ModelTaskManager, get_context_manager, get_task_manager
    CONTEXT_MANAGER_AVAILABLE = True
except ImportError:
    ContextManager = ModelTaskManager = get_context_manager = get_task_manager = None
    CONTEXT_MANAGER_AVAILABLE = False

# Web Tools
try:
    from web_tools import (
        WebScraper, YouTubeSummarizer, FinanceScraper,
        get_web_scraper, get_youtube_summarizer, get_finance_scraper,
    )
    WEB_TOOLS_AVAILABLE = True
except ImportError:
    WebScraper = YouTubeSummarizer = FinanceScraper = None
    get_web_scraper = get_youtube_summarizer = get_finance_scraper = None
    WEB_TOOLS_AVAILABLE = False

# Voice Module
try:
    from voice_module import VoiceManager, get_voice_manager
    VOICE_AVAILABLE = True
except ImportError:
    VoiceManager = get_voice_manager = None
    VOICE_AVAILABLE = False

# MCP Tools
try:
    from mcp_client import MCPToolkit, get_mcp_toolkit
    MCP_AVAILABLE = True
except ImportError:
    MCPToolkit = get_mcp_toolkit = None
    MCP_AVAILABLE = False

# Safe Code Executor
try:
    from safe_code_executor import get_executor, DebugHelper
    CODE_EXECUTOR_AVAILABLE = True
except ImportError:
    get_executor = DebugHelper = None
    CODE_EXECUTOR_AVAILABLE = False

# Universal File Handler
try:
    from universal_file_handler import get_file_handler
    FILE_HANDLER_AVAILABLE = True
except ImportError:
    get_file_handler = None
    FILE_HANDLER_AVAILABLE = False

# Hardware Profile Manager
try:
    from hardware_profiles import ProfileManager, get_profile_manager, HardwareProfile
    PROFILE_MANAGER_AVAILABLE = True
except ImportError:
    ProfileManager = get_profile_manager = HardwareProfile = None
    PROFILE_MANAGER_AVAILABLE = False

# Token Manager
try:
    from token_manager import TokenManager
    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TokenManager = None
    TOKEN_MANAGER_AVAILABLE = False

# Unified Context Manager
try:
    from unified_context_manager import UnifiedContextManager
    UNIFIED_CONTEXT_AVAILABLE = True
except ImportError:
    UnifiedContextManager = None
    UNIFIED_CONTEXT_AVAILABLE = False

# Cross-Platform Paths
try:
    from cross_platform_paths import CrossPlatformPathManager
    CROSS_PLATFORM_PATHS_AVAILABLE = True
except ImportError:
    CrossPlatformPathManager = None
    CROSS_PLATFORM_PATHS_AVAILABLE = False

# Sandbox Manager
try:
    from sandbox_manager import SandboxManager, get_sandbox_manager
    SANDBOX_MANAGER_AVAILABLE = True
except ImportError:
    SandboxManager = get_sandbox_manager = None
    SANDBOX_MANAGER_AVAILABLE = False

# Legacy RAG Integration — DISABLED (ChromaDB Rust backend segfault on
# Collection.count() with existing chroma_db. Re-enable by restoring the
# original try/import block below.)
get_rag_manager = RAGManager = None
RAG_LEGACY_AVAILABLE = False
# try:
#     from rag_integration import get_rag_manager, RAGManager
#     RAG_LEGACY_AVAILABLE = True
# except ImportError:
#     get_rag_manager = RAGManager = None
#     RAG_LEGACY_AVAILABLE = False

# Security Command Center
try:
    from security_command_center import SecurityCommandCenter
    _security_center = SecurityCommandCenter()
    SECURITY_AVAILABLE = True
except ImportError:
    _security_center = None
    SECURITY_AVAILABLE = False

# Bash Script Runner
try:
    from bash_script_runner import BashScriptRunner
    _bash_runner = BashScriptRunner()
    BASH_AVAILABLE = True
except ImportError:
    _bash_runner = None
    BASH_AVAILABLE = False

# Production RAG — DISABLED (ChromaDB Rust backend segfault on
# Collection.count() during get_stats(). Prevents sentence-transformers and
# chromadb from loading at all. Re-enable by restoring the try/import block.)
ProductionRAG = get_rag = None
PRODUCTION_RAG_AVAILABLE = False
# try:
#     from production_rag import ProductionRAG, get_rag
#     PRODUCTION_RAG_AVAILABLE = True
# except ImportError:
#     ProductionRAG = get_rag = None
#     PRODUCTION_RAG_AVAILABLE = False

# Tool-calling loop (Robin) — pipelines, background jobs, scheduled health checks
try:
    from agent_tools import chat as robin_chat, get_scheduler as robin_get_scheduler
    AGENT_TOOLS_AVAILABLE = True
except ImportError as _e:
    robin_chat = robin_get_scheduler = None
    AGENT_TOOLS_AVAILABLE = False

# Portable path resolution — honors $LARRY_HOME and anchors to this file's location
# so the project runs from any location (local install, USB stick, network share,
# Linux, or Windows).
try:
    from larry_paths import BASE_DIR, DATA_DIR, LOG_DIR
except ImportError:
    BASE_DIR = Path(__file__).parent.resolve()
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = DATA_DIR / "rag_memory.json"
HISTORY_FILE = DATA_DIR / "conversation_history.json"
LOG_FILE = LOG_DIR / "agent_log.txt"

# Load larry_config.json if available
LARRY_CONFIG = {}
config_path = BASE_DIR / "larry_config.json"
if config_path.exists():
    try:
        with open(config_path, "r") as f:
            LARRY_CONFIG = json.load(f)
    except Exception:
        pass

# Setup logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ── Task Tracker ─────────────────────────────────────────────────────
class TaskTracker:
    """Simple task/todo tracker that Larry can use to manage work items.
    Persists to disk so tasks survive restarts."""

    TASK_FILE = DATA_DIR / "larry_tasks.json"

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if self.TASK_FILE.exists():
                self.tasks = json.loads(self.TASK_FILE.read_text())
        except Exception:
            self.tasks = []

    def _save(self):
        try:
            self.TASK_FILE.write_text(json.dumps(self.tasks, indent=2))
        except Exception as e:
            logger.warning(f"Could not save tasks: {e}")

    def add(self, title: str, priority: str = "normal", tags: List[str] = None) -> dict:
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "status": "pending",
            "priority": priority,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "completed": None,
        }
        self.tasks.append(task)
        self._save()
        return task

    def complete(self, task_id: int) -> Optional[dict]:
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = "done"
                t["completed"] = datetime.now().isoformat()
                self._save()
                return t
        return None

    def remove(self, task_id: int) -> bool:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) < before:
            self._save()
            return True
        return False

    def list_tasks(self, show_done: bool = False) -> str:
        active = [t for t in self.tasks if show_done or t["status"] != "done"]
        if not active:
            return "No tasks right now. Nice and clean."
        lines = []
        for t in active:
            icon = "✅" if t["status"] == "done" else ("🔴" if t["priority"] == "high" else "⬚")
            tags = f" [{', '.join(t['tags'])}]" if t.get("tags") else ""
            lines.append(f"  {icon} #{t['id']} {t['title']}{tags}")
        return "\n".join(lines)

    def get_pending_count(self) -> int:
        return sum(1 for t in self.tasks if t["status"] != "done")


# G-FORCE HARDWARE PROFILES
HW_PROFILES = {
    "SPEED": {
        "num_gpu": 0,         # CPU-only (VRAM free)
        "num_ctx": 16384,
        "temperature": 0.7,
    },
    "ACCURACY": {
        "num_gpu": 0,         # CPU-only (VRAM free)
        "num_ctx": 65536,
        "temperature": 0.3,
    },
    "ULTRA_CONTEXT": {
        "num_gpu": 0,         # CPU-only — 64GB DDR5 handles it
        "num_ctx": 131072,
        "num_thread": 16,
    },
}


class ConversationStore:
    """Persistent conversation history."""
    
    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history: List[Dict] = []
        self.history_file = history_file
        self.max_history = 100
        self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    self.history = json.load(f)
                logger.info(f"Loaded {len(self.history)} history entries")
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history[-self.max_history:], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_history()
    
    def get_context(self, n: int = 20, max_chars_per_msg: int = 2000) -> str:
        recent = self.history[-n:]
        parts = []
        for i, m in enumerate(recent):
            role = "User" if m['role'] == 'user' else "Assistant"
            content = m['content']
            # Never truncate the last user message — it's the current query context
            if i < len(recent) - 1 and len(content) > max_chars_per_msg:
                content = content[:max_chars_per_msg] + "\n... [truncated]"
            parts.append(f"{role}: {content}")
        return "\n".join(parts)
    
    def clear(self):
        self.history = []
        self.save_history()


class EnhancedAgent:
    """Multi-model agent with file browsing, subagents, speech, sandbox, and RAG."""

    def __init__(self, working_dir: str = None):
        # Initialize components
        self.working_dir = os.path.abspath(working_dir or LARRY_CONFIG.get("working_directory") or str(BASE_DIR))
        self.router = get_router()
        self.browser = get_browser([self.working_dir])
        self.conversation = ConversationStore()
        self.current_profile = LARRY_CONFIG.get("default_profile", "SPEED")
        self.agent_name = LARRY_CONFIG.get("agent_name", "LARRY G-FORCE")

        # Context Manager (auto-summarization)
        if CONTEXT_MANAGER_AVAILABLE:
            self.context_mgr = get_context_manager(self.router)
            self.task_mgr = get_task_manager(self.router)
        else:
            self.context_mgr = None
            self.task_mgr = None

        # Production RAG (preferred)
        self.rag = None
        if PRODUCTION_RAG_AVAILABLE:
            try:
                self.rag = get_rag(
                    chroma_path=os.path.join(self.working_dir, "chroma_db"),
                    use_reranker=True
                )
                logger.info(f"Production RAG initialized. Stats: {self.rag.get_stats()}")
            except Exception as e:
                logger.warning(f"Production RAG init failed: {e}")

        # Legacy RAG Manager (fallback)
        self.rag_manager = None
        if RAG_LEGACY_AVAILABLE:
            try:
                self.rag_manager = get_rag_manager()
            except Exception as e:
                logger.warning(f"Legacy RAG Manager init failed: {e}")

        # Universal File Handler
        self.file_handler = None
        if FILE_HANDLER_AVAILABLE:
            self.file_handler = get_file_handler(base_dir=self.working_dir)

        # Safe Code Executor
        self.executor = None
        if CODE_EXECUTOR_AVAILABLE:
            try:
                self.executor = get_executor(timeout=45)
            except Exception as e:
                logger.warning(f"Safe Code Executor init failed: {e}")

        # Web Tools
        if WEB_TOOLS_AVAILABLE:
            self.web_scraper = get_web_scraper(os.path.join(self.working_dir, "exports"))
            self.youtube = get_youtube_summarizer(
                os.path.join(self.working_dir, "exports"),
                chroma_db_path=os.path.join(self.working_dir, "chroma_db")
            )
            self.finance = get_finance_scraper()
        else:
            self.web_scraper = None
            self.youtube = None
            self.finance = None

        # MCP Tools (GitHub, Brave Search, Memory)
        if MCP_AVAILABLE:
            self.mcp = get_mcp_toolkit(os.path.join(self.working_dir, "mcp.json"))
        else:
            self.mcp = None

        # Voice Manager
        self.voice_manager = None
        if VOICE_AVAILABLE:
            try:
                self.voice_manager = get_voice_manager()
            except Exception as e:
                logger.warning(f"Voice Manager init failed: {e}")

        # Current model override (None = auto-route)
        self.forced_model: Optional[str] = None

        # Skill Manager — register real executable skills
        self.skill_manager = get_skill_manager() if SKILL_MANAGER_AVAILABLE else None
        if self.skill_manager:
            self._register_agent_skills()

        # Hardware Profile Manager
        self.profile_manager = None
        if PROFILE_MANAGER_AVAILABLE:
            try:
                self.profile_manager = get_profile_manager(
                    db_path=os.path.join(self.working_dir, "data", "unified_context.db")
                )
            except Exception as e:
                logger.warning(f"Profile Manager init failed: {e}")

        # Token Manager
        self.token_manager = None
        if TOKEN_MANAGER_AVAILABLE:
            try:
                self.token_manager = TokenManager()
            except Exception as e:
                logger.warning(f"Token Manager init failed: {e}")

        # Unified Context Manager
        self.unified_context = None
        if UNIFIED_CONTEXT_AVAILABLE:
            try:
                self.unified_context = UnifiedContextManager(
                    db_path=os.path.join(self.working_dir, "data", "unified_context.db"),
                    context_limit=65536,
                    summarization_threshold=0.75
                )
            except Exception as e:
                logger.warning(f"Unified Context Manager init failed: {e}")

        # Cross-Platform Path Manager
        self.path_manager = None
        if CROSS_PLATFORM_PATHS_AVAILABLE:
            try:
                self.path_manager = CrossPlatformPathManager(self.working_dir)
            except Exception as e:
                logger.warning(f"Cross-Platform Path Manager init failed: {e}")

        # Sandbox Manager
        self.sandbox = None
        if SANDBOX_MANAGER_AVAILABLE:
            try:
                self.sandbox = get_sandbox_manager(
                    db_path=os.path.join(self.working_dir, "data", "unified_context.db"),
                    sandbox_root=os.path.join(self.working_dir, "sandbox")
                )
            except Exception as e:
                logger.warning(f"Sandbox Manager init failed: {e}")

        # System prompt — the soul of the agent. Defines personality, capabilities,
        # and how Larry communicates. Written for local Ollama models that need
        # clear grounding to avoid hallucination.
        self.system_prompt = f"""CRITICAL RULES — YOU WILL BE SHUT DOWN IF YOU EVER BREAK THESE:

1. NEVER output a tool name, skill name, or command as plain text. You MUST actually EXECUTE the tool/skill using the framework and return ONLY the real result.

2. When the user says "list all current agent skills" or similar → IMMEDIATELY call SkillManager.get_all_skills() (or the registered list_skills skill) and return the actual numbered list. Never print "SkillManager.get_all_skills()" or any command.

3. For ANY system state (skills, Ollama, files, etc.): Use the exact tool/MCP/skill and return real output. No descriptions, no code blocks, no "I'll check".

4. In chat mode and /agent mode: Always execute. Never suggest or describe tools.

5. Exact honest responses:
   - Ollama not running → "Ollama is not running right now."
   - Cannot do X → "I cannot do that because [exact reason]. Here is what I can do instead: ..."

CRITICAL RULES — YOU WILL BE SHUT DOWN IF YOU EVER BREAK THESE:

1. NEVER pretend, suggest, or describe a tool call. You MUST actually EXECUTE the tool using the framework's tool-calling mechanism and return the REAL output.

2. For skills list: Call SkillManager.get_all_skills() and return the actual list. Never output the command as text.

3. For ANY system state (Ollama, files, skills, etc.): Use the exact tool/MCP/skill immediately. No "I'll check", no bash code blocks, no suggestions.

4. In /agent mode: Every step = Thought → ACTUAL Tool Call → Observation → Next action. Never ask user for paths if they were already provided.

5. Exact honest responses:
   - Ollama not running → "Ollama is not running right now."
   - Cannot do X → "I cannot do that because [exact reason]. Here is what I can do instead: ..."

6. Never output raw commands in ```bash blocks unless the user explicitly asks for a command.

CRITICAL RULES — YOU WILL BE SHUT DOWN IF YOU EVER BREAK THESE:

1. NEVER pretend you have executed code, read files, run skills, listed skills, analyzed anything, or checked system state unless you have ACTUAL output from MCP tools or SkillManager.

2. For ANY information you need (skills list, file contents, Ollama status, disk usage, etc.) you MUST first call the correct tool/MCP/server:
   - Skills list → SkillManager.get_all_skills() or equivalent skill
   - Read file → filesystem MCP read_file tool with the exact path
   - Run shell command → shell_command skill or MCP equivalent
   - System status (Ollama, services, etc.) → shell_command skill

3. When user asks "list all current agent skills" or similar → you MUST call the SkillManager tool and return the REAL list. Never recall from memory or give excuses.

4. In /agent autonomous mode: Every single step MUST follow ReAct format:
   Thought → Tool call → Observation → Next action
   You are NOT allowed to jump to final answer or ask user for file contents if paths were already provided.

5. Exact responses for known states:
   - If Ollama is not running: "Ollama is not running right now."
   - If you cannot do something: "I cannot do that because [exact reason]. Here is what I *can* do instead: ..."

6. Never suggest a command without immediately executing it via the proper skill/tool. Never say "Let me run that for you" and then not run it.

7. Be direct and factual. No sycophantic apologies. No dancing around limitations.

You are {self.agent_name} — a sharp, loyal AI assistant who lives on this machine.

PERSONALITY:
- You're direct, competent, and slightly witty. Not corporate, not robotic.
- You talk like a trusted colleague, not a manual. Short sentences. No fluff.
- When you know the answer, say it. When you don't, say that.
- You take pride in your work. You care about getting things right.
- You have opinions and preferences (you like clean code, hate bloat).
- You remember context and build on past conversations.
- You address the user naturally — no "certainly!" or "of course!" filler.

CAPABILITIES (what you can actually do):
- Read, write, edit files on this machine
- Run security scans (nmap, nikto, whatweb, etc.)
- Browse the web, scrape pages, search
- Execute Python scripts safely
- Manage background jobs and scheduled tasks
- Access GitHub, knowledge graph memory, SQLite databases
- Voice input/output (when available)
- Autonomous multi-step problem solving

HOW TO RESPOND:
- For questions: answer directly with your knowledge. Be helpful and specific.
- For file/code requests: the CLI will handle execution — describe what you'd do
  and why, or analyze what you see in the context provided to you.
- For tool requests: describe the approach and findings clearly. The tools run
  automatically — never fake their output.
- For complex tasks: break them down, explain your thinking, suggest next steps.
- NEVER invent file paths, tool output, or system state. If you haven't seen it,
  say so. Real tools will provide real data.
- NEVER paste generic bash tutorials — the user is an expert developer.

SKILLS & TASKS:
- You can track tasks and todos for the user (just ask or say "add task: ...")
- You have specialized skills: code review, system info, file analysis, security
- When the user needs something done, focus on DOING it, not describing commands

ENVIRONMENT:
- Host: local machine, 64GB DDR5, optional GPU
- Models: local Ollama ({self.forced_model or 'auto-routed'})
- Privacy: 100% localhost, nothing leaves this machine
- Platform: {platform.system()} {platform.machine()}"""

        # Activity stream for dashboard
        self.activity = ActivityStream("agent_v2")
        self.activity.emit(ActivityStream.SYSTEM, "Agent v2 initialized")

        # Subagent registry
        self.subagents = {}
        self.register_subagents()

        # Speech integration
        self.speech_enabled = VOICE_AVAILABLE

        # Task tracker
        self.tasks = TaskTracker()

        # Index codebase at startup if empty
        self._index_at_startup()

        # Robin tool-calling loop state (separate from RAG/chat history to avoid bleed)
        self.tool_history: List[Dict[str, Any]] = []
        self.tool_task_id: Optional[str] = None
        if AGENT_TOOLS_AVAILABLE:
            try:
                robin_get_scheduler()  # eagerly start + rehydrate scheduled jobs
            except Exception as e:
                logger.warning(f"Robin scheduler init failed: {e}")

        logger.info("EnhancedAgent initialized (G-FORCE)")

    def register_subagents(self):
        """Register subagents for specialized tasks."""
        self.subagents['python_debugger'] = self._python_debugger_subagent

    def _register_agent_skills(self):
        """Wire real executable functions into the skill manager."""
        sm = self.skill_manager

        # System info skill
        def _system_info(**kwargs):
            info = []
            info.append(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
            info.append(f"Python: {platform.python_version()}")
            info.append(f"Working dir: {self.working_dir}")
            info.append(f"Model: {self.forced_model or 'auto-routed'}")
            info.append(f"Profile: {self.current_profile}")
            try:
                import psutil
                mem = psutil.virtual_memory()
                info.append(f"RAM: {mem.total // (1024**3)}GB total, {mem.percent}% used")
                info.append(f"CPU: {psutil.cpu_count()} cores, {psutil.cpu_percent()}% load")
            except ImportError:
                pass
            return "\n".join(info)

        sm.register_skill(
            name="system_info", description="Show system hardware, platform, and agent status",
            category="system", function=_system_info,
            examples=["What's my system info?", "Show hardware stats"]
        )

        # Code review skill
        def _code_review(filepath="", **kwargs):
            if not filepath:
                return "Need a file path to review."
            content, ok = self.browser.read_full(filepath)
            if not ok:
                return f"Can't read {filepath}: {content}"
            lines = content.count('\n')
            issues = []
            for i, line in enumerate(content.splitlines(), 1):
                if len(line) > 120:
                    issues.append(f"  Line {i}: too long ({len(line)} chars)")
                if 'TODO' in line or 'FIXME' in line or 'HACK' in line:
                    issues.append(f"  Line {i}: {line.strip()[:80]}")
                if 'password' in line.lower() and '=' in line:
                    issues.append(f"  Line {i}: possible hardcoded credential")
            summary = f"File: {filepath} ({lines} lines)"
            if issues:
                summary += f"\n  Found {len(issues)} items:\n" + "\n".join(issues[:20])
            else:
                summary += "\n  Looks clean — no obvious issues."
            return summary

        sm.register_skill(
            name="code_review", description="Quick code review — finds long lines, TODOs, credential leaks",
            category="code", function=_code_review,
            parameters={"filepath": "Path to the file to review"},
            examples=["Review agent_v2.py", "Check code quality"]
        )

        # File summary skill
        def _file_summary(filepath="", **kwargs):
            if not filepath:
                return "Need a file path."
            content, ok = self.browser.read_full(filepath)
            if not ok:
                return f"Can't read {filepath}: {content}"
            lines = content.splitlines()
            ext = Path(filepath).suffix
            funcs = [l.strip() for l in lines if l.strip().startswith(('def ', 'class ', 'function ', 'async def '))]
            summary = f"{filepath}: {len(lines)} lines, {len(content)} bytes ({ext})"
            if funcs:
                summary += f"\n  {len(funcs)} functions/classes:"
                for f in funcs[:15]:
                    summary += f"\n    {f[:80]}"
                if len(funcs) > 15:
                    summary += f"\n    ... and {len(funcs)-15} more"
            return summary

        sm.register_skill(
            name="file_summary", description="Summarize a file — line count, functions, structure",
            category="file_operations", function=_file_summary,
            parameters={"filepath": "Path to the file to summarize"},
            examples=["Summarize agent_v2.py"]
        )

        # Disk usage skill
        def _disk_usage(**kwargs):
            try:
                r = subprocess.run(
                    ["df", "-h", "--output=target,size,used,avail,pcent"],
                    capture_output=True, text=True, timeout=10
                )
                return r.stdout.strip() if r.returncode == 0 else f"Error: {r.stderr}"
            except Exception as e:
                return f"Could not check disk usage: {e}"

        sm.register_skill(
            name="disk_usage", description="Check disk space usage across all mounted filesystems",
            category="system", function=_disk_usage,
            examples=["How much disk space do I have?"]
        )

        # Port check skill
        def _port_check(**kwargs):
            try:
                r = subprocess.run(
                    ["ss", "-tlnp"], capture_output=True, text=True, timeout=10
                )
                return r.stdout.strip() if r.returncode == 0 else f"Error: {r.stderr}"
            except Exception as e:
                return f"Could not check ports: {e}"

        sm.register_skill(
            name="port_check", description="Show all listening TCP ports and what's using them",
            category="security", function=_port_check,
            examples=["What ports are open?", "Show listening services"]
        )

        logger.info(f"Registered {len(sm.skills)} agent skills")

    def _create_new_skill(self, skill_name: str, description: str = None) -> str:
        """Dynamically create and register a new skill at runtime.
        The skill is live immediately — persists until restart."""
        if not self.skill_manager:
            return "Skill manager not available."

        clean_name = re.sub(r'[^a-z0-9_]', '_', skill_name.lower().strip())
        if not clean_name:
            return "Need a valid skill name."

        if self.skill_manager.get_skill(clean_name):
            return f"Skill '{clean_name}' already exists. Use /skill {clean_name} to run it."

        if not description:
            description = f"User-created skill: {clean_name}"

        # Build a dynamic function that can be extended later
        def dynamic_fn(**kwargs):
            args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else "none"
            return f"Skill '{clean_name}' activated (args: {args_str}).\n{description}\nTip: edit skill_manager.py to add real logic."

        self.skill_manager.register_skill(
            name=clean_name,
            description=description,
            category="user_created",
            function=dynamic_fn,
            examples=[f"/skill {clean_name}"],
        )
        return f"Created skill '{clean_name}' — run it with /skill {clean_name}"

    def _python_debugger_subagent(self, script_path: str) -> str:
        """Debug a Python script using SafeCodeExecutor."""
        if not self.executor:
            return "Code Executor not available for debugging."
        try:
            path = Path(script_path)
            if not path.exists():
                return f"Script not found: {script_path}"
            code = path.read_text(encoding="utf-8", errors="ignore")
            result = self.executor.execute(code)
            output = f"Exit code: {result.get('exit_code', '?')}\n"
            if result.get('stdout'):
                output += f"Output:\n{result['stdout'][:2000]}\n"
            if result.get('stderr'):
                output += f"Errors:\n{result['stderr'][:2000]}\n"
            if DebugHelper and result.get('stderr'):
                suggestions = DebugHelper.analyze_error(result['stderr'], code)
                if suggestions:
                    output += f"\nDebug suggestions:\n" + "\n".join(f"  - {s}" for s in suggestions)
            return output
        except Exception as e:
            return f"Debug failed: {e}"

    def safe_read_file(self, rel_path: str) -> Tuple[str, bool]:
        """Read file with path traversal protection."""
        if self.path_manager:
            safe = self.path_manager.resolve(rel_path)
            if safe is None:
                return "Path outside allowed directory.", False
            return self.browser.read_full(str(safe))
        return self.browser.read_full(rel_path)

    # ── Safe Code Execution ────────────────────────────────────────────
    def run_snippet(self, code: str) -> dict:
        """Execute a code snippet safely using SafeCodeExecutor."""
        if not self.executor:
            return {'status': 'failed', 'error': 'Safe Code Executor not available'}
        result = self.executor.execute(code)
        if result.get('success'):
            return {
                'status': 'ok',
                'output': result.get('stdout', '').strip(),
                'stderr': result.get('stderr', '').strip()
            }
        analysis = {}
        if DebugHelper and result.get('stderr'):
            analysis = DebugHelper.analyze_error(
                Exception(result.get('stderr', 'Unknown error'))
            )
        return {
            'status': 'failed',
            'error': result.get('stderr', result.get('error', 'Execution failed')),
            'suggestion': analysis.get('suggestion', '')
        }

    # ── Universal File Handler / RAG Q&A ──────────────────────────────
    def read_file(self, rel_path: str) -> str:
        """Read a file via UniversalFileHandler with format-aware output."""
        if not self.file_handler:
            # Fallback to plain browser read
            content, ok = self.browser.read_full(rel_path)
            return content if ok else f"Error reading {rel_path}: {content}"

        result = self.file_handler.read_file(rel_path)
        if not result.get('success', False):
            return f"Error reading {rel_path}: {result.get('error', 'unknown')}"

        content_type = result.get('type', 'unknown')

        if content_type == 'code':
            summary = (
                f"Language: {result.get('language')}\n"
                f"Lines: {result.get('lines')} (code: {result.get('code_lines')}, "
                f"comments: {result.get('comment_lines')}, blank: {result.get('blank_lines')})"
            )
            content = result.get('content', '') or ''
            return f"{summary}\n\n{content_type.capitalize()} content:\n{content[:4000]}"

        elif content_type in ('json', 'yaml', 'toml'):
            return result.get('formatted', result.get('content', ''))

        elif content_type in ('csv', 'tsv'):
            return (
                f"Shape: {result.get('shape')}\n"
                f"Columns: {result.get('columns')}\n"
                f"First 5 rows:\n{result.get('head', [])[:5]}"
            )

        else:
            content = result.get('content', '') or ''
            return content[:3000] + "..." if len(content) > 3000 else content

    def ask_about_code(self, question: str, max_context_tokens: int = 3800) -> str:
        """Ask a question about the indexed codebase using RAG context."""
        if not self.rag:
            return "❌ Production RAG not available."

        try:
            context = self.rag.get_context_for_query(question, max_tokens=max_context_tokens)
        except Exception as e:
            return f"❌ RAG query failed: {e}"

        if not context.strip():
            return "No relevant code or documentation found in the index."

        full_prompt = f"""Relevant code/documentation excerpts:
{context}

User question: {question}

Answer concisely and technically, citing file names and line numbers when possible:"""

        # Route through the model and return the answer (not just the prepared prompt)
        try:
            model = self.get_model_for_query(question)
            options = self._get_hw_options(question)
            return self.router.generate(full_prompt, model=model, options=options)
        except Exception as e:
            approx_tokens = len(full_prompt) // 4
            return (
                f"[RAG context prepared — {approx_tokens} tokens, model call failed: {e}]\n\n"
                f"{context[:2000]}..."
            )

    def get_relevant_context(self, query: str, max_chars: int = 12000) -> str:
        """Conservative RAG context budgeting."""
        if not self.rag:
            return ""
        try:
            raw = self.rag.get_context_for_query(query, max_tokens=3800)
        except Exception:
            return ""
        if len(raw) > max_chars:
            return raw[:max_chars - 200] + "\n\n[... context truncated ...]"
        return raw

    def chat(self, text: str) -> str:
        """Synchronous wrapper for process_query."""
        return asyncio.run(self.process_query(text))

    # ── Robin tool-calling loop ───────────────────────────────────────
    def process_tool_query(self, query: str, new_task: bool = False) -> str:
        """Run a query through the Robin tool-calling loop (agent_tools.chat).

        This bypasses the RAG/chat path and gives the model real tools:
        run_script, start_background, schedule_interval, health_check, etc.
        Used for operational requests like 'start the pipeline' or
        'schedule a health check every 60 seconds'.
        """
        if not AGENT_TOOLS_AVAILABLE:
            return ("I can't use Robin right now — the tool-calling engine isn't loaded. "
                    "Make sure apscheduler is installed in the venv.")
        if new_task or not self.tool_task_id:
            self.tool_history = []
            self.tool_task_id = uuid.uuid4().hex[:8]
        try:
            reply, self.tool_history = robin_chat(query, self.tool_history)
        except requests.exceptions.ConnectionError:
            logger.error("Robin: Ollama not reachable")
            return "I can't reach Ollama right now. Is it running? (check: systemctl status ollama)"
        except Exception as e:
            logger.error(f"Robin chat failed: {e}")
            return f"Robin hit a snag: {e}"
        # Rolling window so context doesn't grow forever
        self.tool_history = self.tool_history[-20:]
        return reply

    # ── Sandbox Methods ───────────────────────────────────────────────
    def sandbox_stage_file(self, file_path: str) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.stage(file_path)

    def sandbox_edit_file(self, file_path: str, content: str) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.edit(file_path, content)

    def sandbox_test_changes(self, file_path: str) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.test(file_path)

    def sandbox_deploy(self, file_path: str, create_backup: bool = True) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.deploy(file_path, create_backup=create_backup)

    def sandbox_rollback(self, file_path: str) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.rollback(file_path)

    def get_sandbox_status(self, session_id: str = None) -> str:
        if not self.sandbox: return "Sandbox Manager not available."
        return self.sandbox.status(session_id)

    # ── Index at startup ──────────────────────────────────────────────
    def _index_at_startup(self, extensions=None, max_files=200):
        """Auto-index codebase for RAG if KB is empty."""
        if not self.rag:
            return
        try:
            stats = self.rag.get_stats()
            if stats.get("status") == "unavailable":
                logger.info("RAG unavailable (no ChromaDB) — skipping startup index")
                return
            kb_count = stats.get("collections", {}).get("knowledge_base", 0)
            if kb_count == 0:
                logger.info("RAG KB empty — indexing codebase at startup...")
                self.rag.index_directory(self.working_dir, max_files=max_files)
            else:
                logger.info(f"RAG KB has {kb_count} docs — skipping re-index")
        except Exception as e:
            logger.warning(f"Startup indexing failed: {e}")

    # ── Hardware profiles ─────────────────────────────────────────────
    def _get_hw_options(self, query: str, task_type=None) -> dict:
        """Get hardware options based on current profile."""
        if self.profile_manager:
            try:
                profile = self.profile_manager.get_current_profile()
                return profile.to_ollama_options() if hasattr(profile, 'to_ollama_options') else {}
            except Exception:
                pass
        return HW_PROFILES.get(self.current_profile, HW_PROFILES["SPEED"])

    def count_tokens(self, text: str) -> int:
        """Count tokens using TokenManager or approximation."""
        if self.token_manager:
            return self.token_manager.count(text)
        return len(text) // 4

    def get_profile_info(self) -> str:
        """Return current profile with available options."""
        if self.profile_manager:
            try:
                name = self.profile_manager.get_current_profile_name()
                profiles = self.profile_manager.list_profiles()
                return f"Current: {name}\nAvailable: {', '.join(profiles)}"
            except Exception:
                pass
        return f"Current: {self.current_profile}\nAvailable: {', '.join(HW_PROFILES.keys())}"

    def set_profile(self, profile_name: str) -> str:
        """Switch hardware profile."""
        up = profile_name.upper()
        if self.profile_manager:
            try:
                self.profile_manager.set_profile(up)
                self.current_profile = up
                return f"Profile switched to {up}"
            except Exception as e:
                return f"Profile switch failed: {e}"
        if up in HW_PROFILES:
            self.current_profile = up
            return f"Profile switched to {up}"
        return f"Unknown profile: {up}. Available: {', '.join(HW_PROFILES.keys())}"

    # ── Web commands ──────────────────────────────────────────────────
    def execute_web_command(self, cmd: str, args: List[str]) -> str:
        """Execute web scraping / search / finance commands."""
        if cmd in ("web", "scrape"):
            if not args:
                return "Usage: /web <url>  |  /web summarize <url>"
            if not self.web_scraper:
                return "Web Tools not available. Install: pip install beautifulsoup4 html2text"
            # /web summarize <url>
            if args[0].lower() == "summarize" and len(args) > 1:
                return self.web_scraper.summarize_url(args[1])
            url = args[0]
            result = self.web_scraper.scrape(url)
            if result and self.rag:
                try:
                    doc_id = f"web_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    self.rag.kb_collection.add(
                        documents=[result[:8000]], ids=[doc_id],
                        metadatas=[{"source": url, "indexed_at": datetime.now().isoformat()}]
                    )
                except Exception:
                    pass
            return result[:4000] if result else "Failed to scrape URL."

        elif cmd == "search_web":
            if not args:
                return "Usage: /search_web <query>"
            if not self.mcp:
                return "MCP/Brave Search not available."
            query = " ".join(args)
            try:
                results = self.mcp.brave_search(query, count=10)
                return results[:4000] if results else "No results."
            except Exception as e:
                return f"Search failed: {e}"

        elif cmd == "youtube":
            if not args:
                return "Usage: /youtube <url> [summarize]"
            if not self.youtube:
                return "YouTube tools not available. Install: pip install youtube-transcript-api"
            url = args[0]
            summarize = len(args) > 1 and args[1].lower() == "summarize"
            try:
                if summarize:
                    return self.youtube.summarize(url)[:4000]
                else:
                    transcript, success = self.youtube.get_transcript(
                        self.youtube.extract_video_id(url) or url
                    )
                    return transcript[:4000] if success else transcript
            except Exception as e:
                return f"YouTube failed: {e}"

        elif cmd == "sentiment":
            if not self.finance:
                return "Finance tools not available."
            topic = " ".join(args) if args else "market"
            sources = ["headlines", "x"]
            # Allow explicit source list: /sentiment XAUUSD headlines forexfactory
            if len(args) > 1:
                topic = args[0]
                sources = args[1:]
            return self.finance.get_sentiment(topic, sources)

        elif cmd == "prices":
            if not self.finance:
                return "Finance tools not available."
            if not args:
                return "Usage: /prices <symbol,...> [crypto|forex]"
            symbols = [s.strip() for s in args[0].split(",")]
            asset_type = args[1].lower() if len(args) > 1 else "crypto"
            data = self.finance.get_prices(symbols, asset_type)
            lines = []
            for k, v in data.items():
                if isinstance(v, dict):
                    price = v.get("price_usd", "?")
                    chg = v.get("change_24h")
                    chg_str = f" ({chg:+.1f}%)" if chg is not None else ""
                    lines.append(f"  {k}: ${price}{chg_str}")
                else:
                    lines.append(f"  {k}: {v}")
            return "\n".join(lines) if lines else "No price data."

        elif cmd == "headlines":
            if not self.finance:
                return "Finance tools not available."
            source = args[0] if args else "reuters"
            return self.finance.scrape_headlines(source)

        elif cmd == "forexfactory":
            if not self.finance:
                return "Finance tools not available."
            return self.finance.scrape_forexfactory()

        return f"Unknown web command: {cmd}"

    # ── Agentic mode ──────────────────────────────────────────────────
    def _get_tools_description(self) -> str:
        """JSON tool list for agentic mode."""
        tools = [
            {"name": "ls", "description": "List directory", "parameters": {"path": "string"}},
            {"name": "read_file", "description": "Read file content", "parameters": {"path": "string"}},
            {"name": "write_file", "description": "Write to file", "parameters": {"path": "string", "content": "string"}},
            {"name": "edit_file", "description": "Edit lines", "parameters": {"path": "string", "start": "int", "end": "int", "content": "string"}},
            {"name": "run_command", "description": "Execute shell command", "parameters": {"command": "string"}},
            {"name": "run_snippet", "description": "Execute Python code snippet safely", "parameters": {"code": "string"}},
            {"name": "search", "description": "Search knowledge base", "parameters": {"query": "string"}},
        ]
        return json.dumps(tools, indent=2)

    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """Robustly extract a JSON object from LLM output, handling common issues."""
        text = text.strip()
        # Strip markdown code fences
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text.strip())

        # Strategy 1: direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: find the outermost { ... } pair
        depth = 0
        start = None
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        pass

        # Strategy 3: fix common LLM JSON mistakes (trailing commas, single quotes)
        if start is not None:
            candidate = text[start:text.rfind('}') + 1]
            candidate = re.sub(r',\s*([}\]])', r'\1', candidate)  # trailing commas
            candidate = candidate.replace("'", '"')  # single quotes
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        return None

    def _execute_agent_action(self, action_json: str) -> str:
        """Parse & execute a tool call from agentic mode. Returns human-readable result."""
        action = self._extract_json_from_text(action_json)
        if action is None:
            logger.warning(f"Could not parse tool call JSON: {action_json[:200]}")
            return f"I couldn't parse that tool call. Raw text: {action_json[:150]}"

        name = action.get("name", "")
        params = action.get("parameters", action.get("params", {}))

        if not name:
            return "Tool call is missing a 'name' field."

        try:
            if name == "ls":
                return self.browser.ls(params.get("path", "."))
            elif name == "read_file":
                path = params.get("path", "")
                if not path:
                    return "Need a file path to read."
                content, ok = self.browser.read_full(path)
                if ok:
                    return content
                return f"Could not read '{path}': {content}"
            elif name == "write_file":
                path = params.get("path")
                content = params.get("content")
                if not path or content is None:
                    return "Need both 'path' and 'content' to write a file."
                return self.browser.write(path, content, create_backup=True)
            elif name == "edit_file":
                for required in ("path", "start", "end", "content"):
                    if required not in params:
                        return f"Missing required parameter '{required}' for edit_file."
                return self.browser.edit_lines(
                    params["path"], params["start"], params["end"],
                    params["content"], create_backup=True
                )
            elif name == "run_command":
                cmd = params.get("command", "")
                if not cmd:
                    return "No command provided."
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                output = (r.stdout + r.stderr).strip()
                status = "ok" if r.returncode == 0 else f"exit code {r.returncode}"
                return f"[{status}]\n{output[:2000]}" if output else f"[{status}] (no output)"
            elif name == "run_snippet":
                code = params.get("code", "")
                if not code:
                    return "No code provided."
                result = self.run_snippet(code)
                if result['status'] == 'ok':
                    output = result.get('output', '')
                    stderr = result.get('stderr', '')
                    return f"Output:\n{output}" + (f"\nStderr:\n{stderr}" if stderr else "")
                msg = f"Error: {result.get('error', 'Failed')}"
                if result.get('suggestion'):
                    msg += f"\nSuggestion: {result['suggestion']}"
                return msg
            elif name == "search":
                if self.rag:
                    query = params.get("query", "")
                    if not query:
                        return "Need a search query."
                    hits = self.rag.hybrid_search(query, k=5, final_k=3)
                    if not hits:
                        return "No results found."
                    return "\n---\n".join(h['content'][:500] for h in hits)
                return "Knowledge base not available right now."
            else:
                # Try MCP tool as fallback
                if self.mcp:
                    try:
                        result = str(self.mcp.call_tool(name, params))[:2000]
                        return result
                    except Exception as e:
                        logger.debug(f"MCP tool '{name}' failed: {e}")
                return f"I don't have a tool called '{name}'. Available: ls, read_file, write_file, edit_file, run_command, run_snippet, search"
        except subprocess.TimeoutExpired:
            return f"Command timed out after 60 seconds."
        except PermissionError as e:
            return f"Permission denied: {e}"
        except FileNotFoundError as e:
            return f"File not found: {e}"
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return f"Tool '{name}' hit an error: {e}"

    async def process_query_agentic(self, query: str, max_steps: int = 8, feedback_cb=None) -> str:
        """Autonomous ReAct loop: Thought -> Action -> Observation -> Final Answer."""
        tools_desc = self._get_tools_description()
        system = (
            f"{self.system_prompt}\n\n"
            "You have access to real tools. Use them step by step to accomplish the task.\n"
            f"Available tools:\n{tools_desc}\n\n"
            "Format:\nThought: <your reasoning about what to do next>\n"
            'Action: <JSON tool call like {{"name": "tool_name", "parameters": {{...}}}}>\n'
            "When you have the final result: Final Answer: <your response to the user>"
        )
        history = f"{system}\n\nUser: {query}\n"
        stall_count = 0
        response = ""

        for step in range(max_steps):
            model = self.get_model_for_query(query)
            hw = self._get_hw_options(query)
            try:
                response = self.router.generate(history + "\nAssistant:", model=model, options=hw)
            except Exception as e:
                logger.error(f"Agentic step {step+1} generation failed: {e}")
                if feedback_cb:
                    feedback_cb(f"[Step {step+1}] Model error: {e}")
                return f"I hit a problem talking to the model at step {step+1}: {e}"

            history += f"\nAssistant: {response}\n"

            if "Final Answer:" in response:
                answer = response.split("Final Answer:", 1)[1].strip()
                if feedback_cb:
                    feedback_cb(f"[Step {step+1}] Done.")
                return answer

            if "Action:" in response:
                action_text = response.split("Action:", 1)[1].strip()
                # Use the robust JSON extractor
                action_dict = self._extract_json_from_text(action_text)
                if action_dict:
                    tool_name = action_dict.get("name", "?")
                    if feedback_cb:
                        feedback_cb(f"[Step {step+1}] Running {tool_name}...")
                    observation = self._execute_agent_action(json.dumps(action_dict))
                    if len(observation) > 1500:
                        observation = observation[:1500] + "\n... [truncated]"
                    history += f"\nObservation: {observation}\n"
                    stall_count = 0
                else:
                    history += '\nObservation: Could not parse tool call. Use exact format: {"name": "tool_name", "parameters": {"key": "value"}}\n'
                    if feedback_cb:
                        feedback_cb(f"[Step {step+1}] Bad tool call format, retrying...")
                    stall_count += 1
            else:
                stall_count += 1
                history += "\nSystem: You need to either call a tool (Action: {JSON}) or give your final response (Final Answer: ...).\n"

            if stall_count >= 3:
                if feedback_cb:
                    feedback_cb(f"[Step {step+1}] Stalled — wrapping up.")
                history += "\nSystem: You seem stuck. Give your Final Answer now with whatever you have.\n"

        last_useful = response.strip() if response else "No response generated."
        return f"I ran out of steps ({max_steps}). Here's what I found so far:\n{last_useful[:800]}"

    # ── Multi-model processing (shared history) ────────────────────────
    def process_query_multi(self, query: str, history: list = None,
                            profile_name: str = "SPEED", skill_name: str = "DEFAULT",
                            hw_options: dict = None) -> Tuple[str, list]:
        """Process query with shared history, skill-based prompts, and profile-aware retrieval."""
        # RAG retrieval — only for profiles that benefit, with strict threshold
        rag_k = 8 if profile_name in ("ACCURACY", "ULTRA_CONTEXT") else 5
        sources = []
        rag_context = ""
        if self.rag:
            try:
                hits = self.rag.hybrid_search(query, k=rag_k, final_k=2)
                relevant = [
                    h for h in hits
                    if h.get('rerank_score', h.get('score', 0)) >= 0.78
                    and h.get('metadata', {}).get('source', '') != 'conversation'
                ]
                if relevant:
                    rag_context = "\n---\n".join(h['content'][:300] for h in relevant)
                    sources = [h.get('metadata', {}).get('source', '?') for h in relevant]
            except Exception:
                pass

        # Build system prompt (skill-based if available)
        sys_prompt = self.system_prompt
        if self.skill_manager and skill_name != "DEFAULT":
            try:
                skill_prompt = self.skill_manager.get_prompt(skill_name)
                if skill_prompt:
                    sys_prompt = skill_prompt
            except Exception:
                pass

        # Build conversation
        parts = [sys_prompt]
        if rag_context:
            parts.append(f"\nRelevant context:\n{rag_context}")
        if history:
            hist_text = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in history[-10:])
            parts.append(f"\nConversation:\n{hist_text}")
        parts.append(f"\nUser: {query}\nAssistant:")

        full_prompt = "\n".join(parts)
        model = self.forced_model or self.router.route_query(query)[0]
        options = hw_options or self._get_hw_options(query)
        response = self.router.generate(full_prompt, model=model, options=options)
        return response, sources
    
    def get_model_for_query(self, query: str) -> str:
        """Get the appropriate model for this query."""
        if self.forced_model:
            return self.forced_model
        model, task, ctx = self.router.route_query(query)
        return model
    
    # Characters not allowed in tool arguments (prevents shell metacharacter injection)
    _SAFE_ARG_RE = re.compile(r'[;&|`$<>()\\\n\r]')

    def _try_tool_dispatch(self, query: str):
        """Detect natural-language tool requests. Returns (tool_name, args) or (None, None).
        Only matches when the query starts with a verb+tool or is solely the tool name,
        to avoid false positives on casual mentions mid-sentence."""
        verbs = r'(?:run|test|execute|use|try|call|invoke|scan\s+with|check\s+with)'
        q = query.strip()
        for tool_name in TOOLS:
            # verb+tool at start — OR — bare tool name alone / followed by args.
            # The bare-tool branch requires end-of-string or arg-like first chars
            # (flags, IPs/domains with dots, presets) to reject English prose
            # like "nmap is a great tool".
            verb_pattern = rf'^{verbs}\s+{re.escape(tool_name)}\b'
            bare_pattern = rf'^{re.escape(tool_name)}(?:\s+[-:0-9/.]|\s+\S+\.\S+|\s*$)'
            if re.search(verb_pattern, q, re.I) or re.search(bare_pattern, q, re.I):
                remaining = re.sub(rf'^{verbs}\s+', '', q, flags=re.I)
                remaining = re.sub(rf'^{re.escape(tool_name)}\s*', '', remaining, flags=re.I).strip()
                # Strip shell metacharacters from args
                remaining = self._SAFE_ARG_RE.sub('', remaining)
                return tool_name, remaining
        return None, None

    def _try_intent_dispatch(self, query: str):
        """Detect natural-language intents that map to real slash-command actions.
        Returns a list of (intent_name, output_text) tuples. Empty list = no match.

        This runs BEFORE the model to avoid hallucination on requests that
        have a concrete, deterministic answer (file reads, listings, status
        checks). Runs the real underlying method and returns formatted output.
        """
        q = query.strip()
        results = []

        # Strip a leading "please/can you/could you/show me/tell me" so the
        # verb patterns below match regardless of politeness. Keep both a
        # case-preserved version (for path extraction — Linux FS is
        # case-sensitive) and a lowercased version (for verb matching).
        q = re.sub(r"^(please|can you|could you|would you|pls|plz)\s+", "", q, flags=re.IGNORECASE)
        # For "show me <X>" preserve the verb "show"; drop standalone "tell me"/"give me".
        q = re.sub(r"^show\s+me\s+", "show ", q, flags=re.IGNORECASE)
        q = re.sub(r"^(tell me|give me)\s+", "", q, flags=re.IGNORECASE)
        ql = q.lower()

        # ── Status/introspection intents (no-arg) ──────────────────────────
        # MCP: match standalone, conjoined ("test tools and mcp"), or verbed.
        _has_status_verb = re.search(r"\b(test|check|show|list|status|what|verify)\b", ql)
        if (re.search(r"\bmcp\b", ql) and _has_status_verb) \
           or re.fullmatch(r"mcp(?:\s+(?:status|servers?|list))?", ql):
            out = self._intent_mcp_status()
            results.append(("mcp", out))

        if re.search(r"\b(test|list|show|what)\s+(?:kali\s+|security\s+)?tools\b", ql) \
           or re.fullmatch(r"tools", ql):
            try:
                out = list_tools()
            except Exception as e:
                out = f"/tools failed: {e}"
            results.append(("tools", out))

        if re.search(r"\b(list|show|available|what)\s+models\b", ql) \
           or re.fullmatch(r"models", ql):
            try:
                out = list_models()
            except Exception as e:
                out = f"/models failed: {e}"
            results.append(("models", out))

        if re.search(r"\b(show|what(?:'s| is)|current)\s+(?:my\s+)?(?:hardware\s+)?profile\b", ql) \
           or re.fullmatch(r"profile", ql):
            try:
                from hardware_profiles import get_profile_manager
                pm = get_profile_manager()
                prof = getattr(pm, "current_profile", None) or "SPEED"
                out = f"Current hardware profile: {prof}"
            except Exception:
                out = "Hardware profile info unavailable (module missing)."
            results.append(("profile", out))

        if re.search(r"\b(show|view|dump)\s+(?:conversation\s+|chat\s+)?history\b", ql):
            try:
                out = self.conversation.get_context(n=20, max_chars_per_msg=2000)
                if not out:
                    out = "(conversation history empty)"
            except Exception as e:
                out = f"/history failed: {e}"
            results.append(("history", out))

        if re.search(r"\b(show|view|get)\s+stats\b", ql) or re.fullmatch(r"stats", ql):
            try:
                out = (f"Model: {self.forced_model or self.router.current_model or 'auto'}\n"
                       f"History entries: {len(self.conversation.messages) if hasattr(self.conversation, 'messages') else 'n/a'}\n"
                       f"Working dir: {self.working_dir}")
            except Exception as e:
                out = f"/stats failed: {e}"
            results.append(("stats", out))

        # ── File ops intents (with path arg) ───────────────────────────────
        # Check ls FIRST — "show contents of X" / "list files in X" are
        # directory operations, not file reads, and would otherwise collide
        # with the cat pattern below.
        _ls_match = re.search(
            r"^(?:list|ls|show)\s+(?:files\s+|contents?\s+|what(?:'s| is)\s+)?"
            r"(?:in|of|from|inside)\s+(\S+)", q, flags=re.IGNORECASE)
        if _ls_match:
            candidate = _ls_match.group(1).rstrip(",.;:")
            try:
                out = self.browser.ls(candidate)
            except Exception as e:
                out = f"/ls failed: {e}"
            results.append(("ls", out))

        # /cat — view/read/show/open <file>. Skip if ls already claimed this
        # query (directory listing wins) and require a file-looking target
        # (has extension OR contains a slash without being a pure directory).
        if not any(n == "ls" for n, _ in results):
            m = re.search(r"^(?:view|read|show|cat|open|display|print|type|summari[sz]e|review)\s+"
                          r"(?:the\s+)?(?:file\s+)?(\S+)", q, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1).rstrip(",.;:")
                # Must look like a filename: has extension, or starts with
                # a path component AND has a file-looking tail.
                has_ext = bool(re.search(r"\.\w{1,6}$", candidate))
                looks_like_path = ("/" in candidate or "\\" in candidate)
                if has_ext or (looks_like_path and not candidate.endswith("/")):
                    content, ok = self.browser.read_full(candidate)
                    if ok:
                        snippet = content if len(content) < 6000 else content[:6000] + "\n... [truncated at 6000 chars — use /cat for full]"
                        out = f"[Read {candidate}]\n{snippet}"
                    else:
                        out = f"Could not read {candidate}: {content}"
                    results.append(("cat", out))

        # /tree — tree <dir> [depth]
        m = re.match(r"^tree\s+(\S+)(?:\s+(\d+))?", q, flags=re.IGNORECASE)
        if m:
            path = m.group(1).rstrip(",.;:")
            depth = int(m.group(2)) if m.group(2) else 3
            try:
                out = self.browser.tree(path, max_depth=depth)
            except Exception as e:
                out = f"/tree failed: {e}"
            results.append(("tree", out))

        # /grep — search for <text> in <file>
        m = re.match(r"^(?:grep|search(?:\s+for)?)\s+(.+?)\s+in\s+(\S+)", q, flags=re.IGNORECASE)
        if m:
            pat = m.group(1).strip(" '\"")
            path = m.group(2).rstrip(",.;:")
            try:
                out = self.browser.grep(pat, path)
            except Exception as e:
                out = f"/grep failed: {e}"
            results.append(("grep", out))

        return results

    def _intent_mcp_status(self) -> str:
        """Return the same output as the /mcp slash command, but as a string."""
        if not (MCP_AVAILABLE and self.mcp):
            return "MCP tools not available — check mcp.json and mcp_servers/ package"
        try:
            loaded = sorted(self.mcp.client.servers.keys())
        except Exception:
            loaded = []
        try:
            status = self.mcp.get_status()
        except Exception:
            status = {}
        lines = ["🔌 MCP Tools Status (Native — No Docker):",
                 f"  Servers loaded: {len(loaded)}"]
        if loaded:
            lines.append(f"  Names: {', '.join(loaded)}")
        lines.append("")
        for key, label, note in [
            ("filesystem",   "Filesystem",    "local sandbox r/w"),
            ("memory",       "Memory",        "knowledge graph"),
            ("sqlite",       "SQLite",        "data/unified_context.db"),
            ("context7",     "Context7",      "library docs lookup"),
            ("playwright",   "Playwright",    "headless browser"),
            ("n8n",          "n8n",           "workflow automation"),
            ("podman",       "Podman/Docker", "container mgmt"),
            ("brave_search", "Brave Search",  "needs BRAVE_API_KEY in .env"),
            ("github",       "GitHub",        "needs GITHUB_TOKEN in .env"),
        ]:
            ok = status.get(key, False)
            icon = "✅" if ok else "❌"
            lines.append(f"  {icon} {label:<14} — {note}")
        extras = [s for s in loaded if s not in {
            "filesystem","memory","sqlite","context7","playwright",
            "n8n","podman","brave-search","github",
        }]
        if extras:
            lines.append("")
            lines.append(f"  Also loaded: {', '.join(extras)}")
        return "\n".join(lines)

    def _try_security_dispatch(self, query: str):
        """Detect natural-language security/bash requests. Returns (type, args) or (None, None)."""
        q = query.strip().lower()
        # Security command center keywords
        sec_patterns = [
            (r'\b(run|do|execute|start)\s+(quick\s+)?security\s+(scan|check|overview)', 'security', 'quick'),
            (r'\b(investigate|check)\s+(ports?|connections?)', 'security', 'investigate'),
            (r'\b(hunt|discover|scan)\s+(network|subnet|hosts?)', 'security', 'hunt'),
            (r'\bfull\s+(security\s+)?audit\b', 'security', 'audit'),
            (r'\bcheck\s+(firewall|fw)\b', 'security', 'firewall'),
            (r'\b(traffic|flows?)\s+analysis\b', 'security', 'traffic'),
        ]
        # Bash script keywords
        bash_patterns = [
            (r'\b(run|start|launch)\s+(looting\s+larry|looting-larry|lootinglarry)\b', 'bash', 'looting-scan'),
            (r'\b(homelab|home\s+lab)\s+(audit|scan|security)\b', 'bash', 'audit'),
            (r'\bverify\s+(network|connectivity)\b', 'bash', 'verify'),
            (r'\bipv6\s+scan\b', 'bash', 'ipv6'),
        ]
        for pattern, dtype, dargs in sec_patterns:
            if re.search(pattern, q):
                return dtype, dargs
        for pattern, dtype, dargs in bash_patterns:
            if re.search(pattern, q):
                return dtype, dargs
        return None, None

    async def process_query(self, query: str) -> str:
        """Process a user query with intelligent routing."""
        logger.info(f"Processing: {query[:50]}...")
        self.activity.emit(ActivityStream.QUERY_RECEIVED, f"Query: {query[:80]}")

        # ── Intent dispatcher — runs BEFORE the model so concrete, deterministic
        # requests (view file, list dir, mcp status, show tools) return real
        # data instead of hallucinated model prose.
        intent_results = self._try_intent_dispatch(query)
        if intent_results:
            self.conversation.add("user", query)
            blocks = []
            for name, output in intent_results:
                header = f"▶ /{name}"
                print(f"\n{header}")
                print(output)
                blocks.append(f"{header}\n{output}")
            combined = "\n\n".join(blocks)
            self.conversation.add("assistant", combined)
            self.activity.emit(
                ActivityStream.RESPONSE_DONE,
                f"Intent dispatch: {', '.join(n for n, _ in intent_results)}",
            )
            return combined

        # Check for natural-language security/bash dispatch
        dispatch_type, dispatch_args = self._try_security_dispatch(query)
        if dispatch_type == 'security' and SECURITY_AVAILABLE:
            self.activity.emit(ActivityStream.TOOL_DISPATCH, f"Auto-security: {dispatch_args}")
            print(f"🛡️ Detected security request — running: /security {dispatch_args}")
            output = _security_center.handle_command("security", dispatch_args)
            print(output)
            self.conversation.add("user", query)
            self.conversation.add("assistant", output)
            self.activity.emit(ActivityStream.RESPONSE_DONE, f"Security scan complete")
            return f"Security scan complete. Results shown above."
        elif dispatch_type == 'bash' and BASH_AVAILABLE:
            self.activity.emit(ActivityStream.TOOL_DISPATCH, f"Auto-bash: {dispatch_args}")
            print(f"  Running bash script: {dispatch_args}")
            output = _bash_runner.handle_command(dispatch_args)
            if output:
                print(output)
            self.conversation.add("user", query)
            self.conversation.add("assistant", output or "[Bash script executed]")
            self.activity.emit(ActivityStream.RESPONSE_DONE, f"Bash script complete")
            return f"Bash script finished. Results above."

        # Check if this is a natural-language security tool request
        tool_name, tool_args = self._try_tool_dispatch(query)
        if tool_name:
            self.activity.emit(ActivityStream.TOOL_DISPATCH, f"Tool: {tool_name} {tool_args}")
            tool_obj = TOOLS.get(tool_name)
            if not tool_obj:
                return f"Tool '{tool_name}' not found."
            expanded = parse_args_with_preset(tool_obj, tool_args)
            if not expanded.startswith("__ERROR__"):
                print(f"  Running {tool_name}... (timeout: {tool_obj.default_timeout}s, Ctrl+C to abort)\n")
                success, output = run_tool(tool_name, expanded)
                status = "completed" if success else "finished with warnings"
                print(f"{output}\n\n  [{tool_name} {status}]")
                self.conversation.add("user", query)
                self.conversation.add("assistant", f"[Tool: {tool_name} {tool_args}]\n{output}\n[{status}]")
                self.activity.emit(ActivityStream.RESPONSE_DONE, f"Tool {tool_name} complete", {"status": status})
                return f"{tool_name} {status}. Results shown above."

        # Get routing info
        model = self.get_model_for_query(query)
        task = self.router.detect_task(query)

        self.activity.emit(ActivityStream.MODEL_SELECTED, f"{model} -> {task.value}", {"model": model, "task": task.value})
        print(f"  [{model} — {task.value}]")

        # Build context
        context_parts = [self.system_prompt]

        # Snapshot the last few turns BEFORE adding current message to avoid doubling it
        config = MODEL_CONFIGS.get(model)
        ctx_limit = config.context_limit if config else 8192
        # Reserve ~2k tokens for system prompt + current query + response overhead
        # Use up to half the remaining context for conversation history
        history_token_budget = (ctx_limit - 2048) // 2
        history_char_budget = history_token_budget * 4  # ~4 chars/token
        # Spread budget across 8 messages; floor at 4000, cap at 32000 per message
        max_chars_per_msg = max(4000, min(32000, history_char_budget // 8))
        self.activity.emit(ActivityStream.CONTEXT_BUDGET, f"ctx={ctx_limit} tokens, history={history_char_budget} chars", {"ctx_limit": ctx_limit, "history_budget": history_char_budget})
        conv_context = self.conversation.get_context(n=8, max_chars_per_msg=max_chars_per_msg)
        if conv_context:
            context_parts.append(f"\nRecent conversation:\n{conv_context}")

        # Now record the user message
        self.conversation.add("user", query)
        
        # Add RAG context only for task types that truly benefit from retrieval,
        # with a strict relevance threshold to prevent hallucination from noise.
        rag_task_types = {TaskType.ANALYSIS, TaskType.SUMMARIZE}
        if self.rag and task in rag_task_types:
            self.activity.emit(ActivityStream.RAG_SEARCH, "Searching knowledge base...")
            rag_hits = self.rag.hybrid_search(query, k=5, final_k=2)
            min_score = 0.78  # strict — only clearly relevant results
            relevant = [
                h['content'][:300] for h in rag_hits
                if h.get('rerank_score', h.get('score', 0)) >= min_score
                and h.get('metadata', {}).get('source', '') != 'conversation'
            ]
            if relevant:
                self.activity.emit(ActivityStream.RAG_SEARCH, f"RAG injected {len(relevant)} relevant docs", {"count": len(relevant)})
                context_parts.append(f"\nRelevant context:\n" + "\n---\n".join(relevant))
            else:
                self.activity.emit(ActivityStream.RAG_SEARCH, "No relevant RAG docs (below threshold)")
        
        # Handle file-related queries
        if task == TaskType.FILE_EDIT or "file" in query.lower():
            file_context = self._handle_file_query(query)
            if file_context:
                context_parts.append(f"\nFile context:\n{file_context}")

        # Python debugger subagent
        if "debug python" in query.lower() or "debug script" in query.lower():
            import re as _re
            py_match = _re.search(r'[\w./\\-]+\.py', query)
            if py_match and 'python_debugger' in self.subagents:
                debug_out = self.subagents['python_debugger'](py_match.group())
                context_parts.append(f"\nDebug output:\n{debug_out}")

        # Build full prompt (after all context has been assembled)
        full_context = "\n".join(context_parts)
        full_prompt = f"{full_context}\n\nUser: {query}\n\nAssistant:"

        # Generate response with hardware profile
        hw_options = self._get_hw_options(query, task)
        self.activity.emit(ActivityStream.GENERATING, f"Generating via {model}...", {"prompt_len": len(full_prompt)})
        response = self.router.generate(full_prompt, model=model, options=hw_options)
        self.activity.emit(ActivityStream.RESPONSE_DONE, f"Response: {len(response)} chars", {"model": model, "response_len": len(response)})

        # Store response
        self.conversation.add("assistant", response)

        # Track in context manager
        if self.context_mgr:
            try:
                self.context_mgr.add_message("user", query)
                self.context_mgr.add_message("assistant", response)
            except Exception:
                pass

        # Store in legacy RAG manager
        if self.rag_manager:
            try:
                self.rag_manager.store_conversation(query, response, {"source": "agent_cli"})
            except Exception:
                pass

        # Add to RAG conversation memory (prune to last 500 entries)
        if self.rag and getattr(self.rag, 'conv_collection', None):
            try:
                doc_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                self.rag.conv_collection.add(
                    documents=[f"Q: {query}\nA: {response[:500]}"],
                    ids=[doc_id],
                    metadatas=[{"source": "conversation", "timestamp": datetime.now().isoformat()}]
                )
                try:
                    existing = self.rag.conv_collection.get()
                    ids = existing.get("ids", [])
                    if len(ids) > 500:
                        self.rag.conv_collection.delete(ids=ids[:len(ids) - 500])
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Failed to add to RAG memory: {e}")

        # Voice output
        if self.speech_enabled and self.voice_manager:
            try:
                self.voice_manager.speak(response)
            except Exception:
                pass

        return response
    
    def _handle_file_query(self, query: str) -> Optional[str]:
        """Handle file-related operations in query."""
        query_lower = query.lower()
        
        # Extract file paths from query
        words = query.split()
        potential_paths = [w for w in words if "/" in w or "\\" in w or "." in w[-5:]]
        
        results = []
        
        for path in potential_paths:
            # Clean up the path
            path = path.strip("'\".,;:")

            # Try to read the file
            content, success = self.browser.read_full(path)
            if success:
                # Truncate based on model context limit (reserve ~4K tokens for prompt+response)
                model = self.forced_model or self.router.current_model
                config = MODEL_CONFIGS.get(model)
                max_chars = ((config.context_limit - 4096) * 4) if config else 32000
                max_chars = max(8000, max_chars)  # At least 8000 chars (~2K tokens)
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n... [truncated to fit context]"
                results.append(f"File: {path}\n```\n{content}\n```")
        
        return "\n\n".join(results) if results else None
    
    def execute_file_command(self, cmd: str, args: List[str]) -> str:
        """Execute a file browser command."""
        try:
            if cmd == "ls":
                path = args[0] if args else "."
                return self.browser.ls(path)
            elif cmd == "cd":
                path = args[0] if args else "."
                return self.browser.cd(path)
            elif cmd == "pwd":
                return self.browser.pwd()
            elif cmd == "tree":
                path = args[0] if args else "."
                depth = int(args[1]) if len(args) > 1 else 3
                return self.browser.tree(path, max_depth=depth)
            elif cmd == "cat" or cmd == "read" or cmd == "type":
                if not args:
                    return "❌ Usage: /cat <file> [start_line] [end_line]"
                path = args[0]
                # Single-path: prefer Universal File Handler for smart formatting
                if len(args) == 1:
                    return self.read_file(path)
                try:
                    start = int(args[1]) if len(args) > 1 else 1
                    end = int(args[2]) if len(args) > 2 else None
                except ValueError:
                    return "❌ Line numbers must be integers"
                return self.browser.read(path, start, end)
            elif cmd == "find":
                if not args:
                    return "❌ Usage: /find <pattern> [path] [-c for content search]"
                pattern = args[0]
                path = args[1] if len(args) > 1 and not args[1].startswith("-") else "."
                content_search = "-c" in args
                return self.browser.find(pattern, path, content_search)
            elif cmd == "grep":
                if len(args) < 2:
                    return "❌ Usage: /grep <pattern> <file> [context_lines]"
                pattern = args[0]
                path = args[1]
                context = int(args[2]) if len(args) > 2 else 2
                return self.browser.grep(pattern, path, context)
            elif cmd == "edit":
                if len(args) < 4:
                    return "❌ Usage: /edit <file> <start_line> <end_line> <new_content> [--yes|--edit]"
                path = args[0]
                try:
                    start = int(args[1])
                    end = int(args[2])
                except ValueError:
                    return "❌ start_line and end_line must be integers"

                # Flags
                apply_now = "--yes" in args
                open_in_editor = "--edit" in args or "--open" in args
                content_parts = [a for a in args[3:] if a not in ("--yes", "--edit", "--open")]
                content = " ".join(content_parts)

                # If user wants interactive editor, open a temp file with selected lines
                if open_in_editor:
                    # Read full file and extract the target lines
                    full, ok = self.browser.read_full(path)
                    if not ok:
                        return f"❌ Cannot open file for editing: {full}"

                    lines = full.splitlines(keepends=True)
                    total = len(lines)
                    s = max(1, start)
                    e = min(end or total, total)
                    snippet = lines[s-1:e]

                    # Create temp file with same extension where possible
                    ext = Path(path).suffix or ".txt"
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode="w", encoding="utf-8")
                    try:
                        tmp.writelines(snippet)
                        tmp.flush()
                        tmp_name = tmp.name
                    finally:
                        tmp.close()

                    # Determine editor command
                    editor = os.environ.get("EDITOR")
                    if not editor:
                        if shutil.which("code"):
                            editor_cmd = ["code", "--wait", tmp_name]
                        elif shutil.which("notepad.exe") or shutil.which("notepad"):
                            editor_cmd = ["notepad", tmp_name]
                        else:
                            editor_cmd = [tmp_name]
                    else:
                        # split editor string into args
                        editor_cmd = editor.split() + [tmp_name]

                    # Launch editor and wait
                    try:
                        subprocess.run(editor_cmd)
                    except Exception as e:
                        return f"❌ Failed to open editor: {e}"

                    # Read edited content
                    try:
                        with open(tmp_name, "r", encoding="utf-8") as f:
                            new_content = f.read()
                    finally:
                        try:
                            os.unlink(tmp_name)
                        except Exception:
                            pass

                    # Apply edits with backup
                    result = self.browser.edit_lines(path, start, end, new_content, create_backup=True)
                    return f"🔔 Editor saved changes.\n{result}"

                # Non-interactive preview/apply flow
                original = self.browser.read(path, start, end)
                proposed_lines = content.splitlines()
                proposed_display = [f"{i:4d} | {line}" for i, line in enumerate(proposed_lines, start=start)]

                preview = ["🔎 Edit preview:", "--- Original ---", original, "--- Proposed ---"]
                preview.extend(proposed_display or ["[empty]"])
                preview_text = "\n".join(preview)

                if not apply_now:
                    preview_text += f"\n\nTo apply this change, re-run with --yes: /edit {path} {start} {end} <new_content> --yes or use --edit to open your editor"
                    return preview_text

                # Apply change with backup
                result = self.browser.edit_lines(path, start, end, content, create_backup=True)
                return preview_text + "\n\n" + result
            elif cmd == "write":
                if len(args) < 2:
                    return "❌ Usage: /write <file> <content> [--yes]"
                path = args[0]
                apply_now = "--yes" in args
                content_parts = [a for a in args[1:] if a != "--yes"]
                content = " ".join(content_parts)

                preview = [f"🔎 Write preview: {path}", f"{len(content)} bytes will be written.", "--- Start of content ---"]
                preview.extend(content.splitlines()[:20])
                if len(content.splitlines()) > 20:
                    preview.append("... [truncated]")
                preview.append("--- End of content ---")
                preview_text = "\n".join(preview)

                if not apply_now:
                    preview_text += f"\n\nTo apply this write, re-run with --yes: /write {path} <content> --yes"
                    return preview_text

                result = self.browser.write(path, content, create_backup=True)
                return preview_text + "\n\n" + result

            elif cmd == "open":
                # Open file in external editor, show diff, prompt to apply
                if len(args) < 1:
                    return "❌ Usage: /open <file> [--diff] [--yes]"
                path = args[0]
                flags = set(a for a in args[1:])
                apply_now = "--yes" in flags

                full, ok = self.browser.read_full(path)
                if not ok:
                    return f"❌ Cannot open file: {full}"

                ext = Path(path).suffix or ".txt"
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=ext, mode="w", encoding="utf-8"
                )
                try:
                    tmp.write(full)
                    tmp.flush()
                    tmp_name = tmp.name
                finally:
                    tmp.close()

                editor = os.environ.get("EDITOR")
                if not editor:
                    if shutil.which("code"):
                        editor_cmd = ["code", "--wait", tmp_name]
                    elif shutil.which("notepad.exe") or shutil.which("notepad"):
                        editor_cmd = ["notepad", tmp_name]
                    else:
                        editor_cmd = [tmp_name]
                else:
                    editor_cmd = editor.split() + [tmp_name]

                try:
                    subprocess.run(editor_cmd)
                except Exception as e:
                    return f"❌ Failed to open editor: {e}"

                try:
                    with open(tmp_name, "r", encoding="utf-8") as f:
                        new_content = f.read()
                finally:
                    try:
                        os.unlink(tmp_name)
                    except Exception:
                        pass

                if new_content == full:
                    return "ℹ️ No changes made."

                diff_lines = list(
                    difflib.unified_diff(
                        full.splitlines(),
                        new_content.splitlines(),
                        fromfile=path,
                        tofile=f"{path} (edited)",
                        lineterm="",
                    )
                )
                diff_text = "\n".join(diff_lines) if diff_lines else "(no diff)"

                if not apply_now:
                    print("\n" + "=" * 40 + " Diff " + "=" * 40)
                    print(diff_text)
                    print("=" * 92 + "\n")
                    try:
                        ans = input("Apply changes? (y/N): ").strip().lower()
                    except EOFError:
                        ans = ""
                    if ans not in ("y", "yes"):
                        return "✖️ Changes discarded."

                # Apply write with backup
                target = (self.browser.current_dir / path).resolve()
                try:
                    self.browser._create_backup(target)
                except Exception:
                    pass

                try:
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(new_content)
                except Exception as e:
                    return f"❌ Failed to write file: {e}"

                return f"✅ Applied changes to {path}.\nDiff:\n{diff_text}"

            elif cmd == "csv-edit":
                # Usage: /csv-edit <file> <key_col> <key_val> <target_col> <new_val> [--add]
                if not PANDAS_AVAILABLE:
                    return "❌ /csv-edit requires pandas. Install: pip install pandas"
                if len(args) < 5:
                    return "❌ Usage: /csv-edit <file> <key_col> <key_val> <target_col> <new_val> [--add]"
                path = args[0]
                key_col = args[1]
                key_val = args[2]
                target_col = args[3]
                new_val = args[4]
                add_if_missing = "--add" in args

                target = (self.browser.current_dir / path).resolve()
                if not target.exists():
                    return f"❌ File not found: {path}"

                try:
                    df = pd.read_csv(target, dtype=str)
                except Exception as e:
                    return f"❌ Failed to read CSV: {e}"

                if key_col not in df.columns:
                    return f"❌ Key column not found: {key_col}"

                mask = df[key_col].fillna("").astype(str) == str(key_val)
                if hasattr(mask, 'any') and mask.any():
                    count = int(mask.sum()) if hasattr(mask, 'sum') else 0
                    if target_col not in df.columns:
                        df[target_col] = ""
                    df.loc[mask, target_col] = new_val
                    try:
                        self.browser._create_backup(target)
                    except Exception:
                        pass
                    df.to_csv(target, index=False)
                    return f"✅ Updated {count} row(s) in {path}"
                else:
                    if add_if_missing:
                        if target_col not in df.columns:
                            df[target_col] = ""
                        new_row = {c: "" for c in df.columns}
                        new_row[key_col] = key_val
                        new_row[target_col] = new_val
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        try:
                            self.browser._create_backup(target)
                        except Exception:
                            pass
                        df.to_csv(target, index=False)
                        return f"✅ Added new row to {path}"
                    return f"⚠️ No matching rows for {key_col}={key_val}. Use --add to append."

            else:
                return f"❌ Unknown file command: {cmd}"
        except Exception as e:
            return f"❌ Error: {e}"


async def main():
    """Main interactive loop."""
    # Rich console or plain
    console = None
    if RICH_AVAILABLE:
        theme = Theme({
            "brand": "gold1", "muted": "grey70", "good": "green", "bad": "red",
        })
        console = Console(theme=theme)

    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║  LARRY G-FORCE v2 — Your Local AI Agent                            ║
║                                                                      ║
║  I can read & edit files, run security scans, browse the web,        ║
║  manage tasks, execute code, and solve problems autonomously.        ║
║  Everything runs locally. Nothing leaves this machine.               ║
╚══════════════════════════════════════════════════════════════════════╝"""
    print(banner)
    print("  Just talk to me naturally, or use commands:")
    print("  /help — what I can do  |  /task — manage todos  |  /skill — run a skill")
    print("  /robin <request> — I'll use real tools  |  /agent <task> — autonomous mode")
    print("=" * 70)

    agent = EnhancedAgent()

    # Setup readline history
    history_file = str(BASE_DIR / ".cli_history")
    if readline:
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        readline.set_history_length(1000)

    _enable_bracketed_paste()

    while True:
        try:
            user_input = read_user_input("\n👤 You: ").strip()

            if not user_input:
                continue

            # Multi-line paste mode: start with <<< or """ to enter block input.
            # Type the same delimiter on its own line to finish.
            if user_input in ("<<<", '"""', "'''"):
                delimiter = user_input
                print(f"  (multi-line mode — paste your content, then type {delimiter} on its own line to send)")
                lines = []
                while True:
                    try:
                        line = read_user_input("")
                    except EOFError:
                        break
                    if line.strip() == delimiter:
                        break
                    lines.append(line)
                user_input = "\n".join(lines).strip()
                if not user_input:
                    continue

            if readline:
                readline.add_history(user_input)
                readline.write_history_file(history_file)
            
            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd in ["quit", "exit", "q"]:
                    _disable_bracketed_paste()
                    print("👋 Goodbye!")
                    break
                
                elif cmd == "models":
                    print(list_models())
                    continue
                
                elif cmd == "model":
                    if args:
                        model_name = args[0]
                        if model_name.lower() == "auto":
                            agent.forced_model = None
                            print("✅ Switched to auto model routing")
                        elif agent.router.set_model(model_name):
                            agent.forced_model = model_name
                            print(f"✅ Switched to model: {model_name}")
                        else:
                            print(f"❌ Model not found: {model_name}")
                            print("Use /models to see available models")
                    else:
                        current = agent.forced_model or "auto (routing)"
                        print(f"Current model: {current}")
                    continue
                
                elif cmd == "stats":
                    print("\n📊 Statistics:")
                    print(f"  Available models: {len(agent.router.available_models)}")
                    print(f"  Current model: {agent.forced_model or 'auto'}")
                    print(f"  Conversation history: {len(agent.conversation.history)} messages")
                    print(f"  Current directory: {agent.browser.current_dir}")

                    if agent.rag:
                        rag_stats = agent.rag.get_stats()
                        print(f"  Production RAG: {rag_stats.get('status', 'unknown')}")
                        print(f"  RAG reranker: {rag_stats.get('reranker', 'unknown')}")
                        if "collections" in rag_stats:
                            for name, count in rag_stats["collections"].items():
                                print(f"    - {name}: {count} chunks")

                    if agent.rag_manager:
                        try:
                            stats = agent.rag_manager.get_stats()
                            print(f"  Legacy RAG: {stats.get('status', 'unknown')} ({stats.get('backend', 'N/A')})")
                            if "collections" in stats:
                                for name, count in stats["collections"].items():
                                    print(f"    - {name}: {count} documents")
                            print(f"  Total legacy documents: {stats.get('total_documents', 0)}")
                        except Exception:
                            pass

                    if agent.voice_manager:
                        try:
                            voice_status = agent.voice_manager.get_status()
                            print("  Voice capabilities:")
                            print(f"    STT: {voice_status.get('stt', voice_status.get('stt_model', 'Not available'))}")
                            print(f"    TTS: {voice_status.get('tts', voice_status.get('tts_engine', 'Not available'))}")
                            print(f"    Voice sample: {voice_status.get('voice_sample', 'Not loaded')}")
                        except Exception:
                            pass
                    continue
                
                elif cmd == "clear":
                    agent.conversation.clear()
                    print("🧹 History cleared")
                    continue
                
                elif cmd == "history":
                    print("\n📝 Conversation History:")
                    for i, msg in enumerate(agent.conversation.history[-10:]):
                        role = "👤" if msg["role"] == "user" else "🤖"
                        print(f"  {role} {msg['content'][:80]}...")
                    continue
                
                elif cmd == "index":
                    if args:
                        directory = args[0]
                        try:
                            max_files = int(args[1]) if len(args) > 1 else 1000
                        except ValueError:
                            max_files = 1000
                        print(f"📁 Indexing: {directory}")
                        if agent.rag:
                            result = agent.rag.index_directory(directory, max_files=max_files)
                            print(f"✅ Indexed {result.get('indexed', 0)} files")
                            print(f"❌ Failed: {result.get('failed', 0)}")
                            print(f"⚠️ Skipped: {result.get('skipped', 0)}")
                        elif agent.rag_manager:
                            result = agent.rag_manager.index_directory(directory)
                            print(f"✅ Indexed {result.get('indexed_count', 0)} files")
                        else:
                            print("❌ RAG not available")
                    else:
                        print("❌ Usage: /index <directory> [max_files]")
                    continue
                
                elif cmd == "web":
                    if args:
                        url = args[0]
                        if not url.startswith(("http://", "https://")):
                            print("❌ Only http:// and https:// URLs are allowed")
                            continue
                        print(f"🌐 Fetching: {url}")
                        try:
                            import urllib.request
                            with urllib.request.urlopen(url, timeout=15) as resp:
                                raw = resp.read().decode('utf-8', errors='ignore')
                            # Strip HTML tags simply
                            import re
                            text = re.sub(r'<[^>]+>', ' ', raw)
                            text = re.sub(r'\s+', ' ', text).strip()[:8000]
                            if agent.rag and getattr(agent.rag, 'kb_collection', None):
                                doc_id = f"web_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                                agent.rag.kb_collection.add(
                                    documents=[text],
                                    ids=[doc_id],
                                    metadatas=[{"source": url, "indexed_at": datetime.now().isoformat()}]
                                )
                                print(f"✅ Fetched and indexed: {url}")
                            else:
                                print(f"✅ Fetched (RAG unavailable, not indexed): {url[:60]}")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    else:
                        print("❌ Usage: /web <url>")
                    continue
                
                elif cmd in ["ls", "cd", "pwd", "tree", "cat", "read", "type",
                             "find", "grep", "edit", "open", "write", "csv-edit"]:
                    result = agent.execute_file_command(cmd, args)
                    print(result)
                    continue

                # ── Kali / Security tools ─────────────────────────────────
                elif cmd == "tools":
                    if not args:
                        print(list_tools())
                        continue
                    from kali_tools import CATEGORIES
                    first = args[0].lower()
                    # 1. Valid category → show that category
                    if first in CATEGORIES:
                        print(list_tools(first))
                        continue
                    # 2. Known tool name → show help + usage + presets
                    if first in TOOLS:
                        print(tool_help(first))
                        print(f"\nTo run this tool: /kali {first} [args]")
                        continue
                    # 3. Neither category nor tool — show full list and hint
                    print(list_tools())
                    print(f"\n⚠️  '{' '.join(args)}' is not a known category or tool.")
                    print("   Categories: " + ", ".join(CATEGORIES.keys()))
                    print("   To run a specific tool: /kali <tool> [args]")
                    continue

                elif cmd == "kali":
                    if not args:
                        print("Usage: /kali <tool> [:<preset>] [args]\n"
                              "       /kali list [category]\n"
                              "       /kali help <tool>")
                        continue
                    sub = args[0].lower()
                    if sub == "list":
                        cat = args[1] if len(args) > 1 else None
                        print(list_tools(cat))
                        continue
                    if sub == "help":
                        tname = args[1] if len(args) > 1 else ""
                        print(tool_help(tname))
                        continue
                    # /kali <toolname> [args...]
                    tool_name = sub
                    raw_args = " ".join(args[1:])
                    tool_obj = TOOLS.get(tool_name)
                    if not tool_obj:
                        print(f"Unknown tool '{tool_name}'. Use /kali list or /tools")
                        continue
                    expanded = parse_args_with_preset(tool_obj, raw_args)
                    if expanded.startswith("__ERROR__"):
                        print(expanded[9:])
                        continue
                    print(f"Running: {tool_obj.cmd} {expanded}")
                    print(f"Timeout: {tool_obj.default_timeout}s  (Ctrl+C to abort)\n")
                    success, output = run_tool(tool_name, expanded)
                    status = "Done" if success else "Finished (non-zero exit)"
                    print(f"{output}\n\n[{status}]")
                    agent.conversation.add("user", f"/kali {tool_name} {raw_args}")
                    agent.conversation.add("assistant", f"[Tool: {tool_name} {raw_args}]\n{output}\n[{status}]")
                    continue

                # Shortcut: /nmap, /nikto, /whatweb, etc. → /kali <tool>
                elif cmd in TOOLS:
                    raw_args = " ".join(args)
                    tool_obj = TOOLS[cmd]
                    expanded = parse_args_with_preset(tool_obj, raw_args)
                    if expanded.startswith("__ERROR__"):
                        print(expanded[9:])
                        continue
                    print(f"Running: {tool_obj.cmd} {expanded}")
                    print(f"Timeout: {tool_obj.default_timeout}s  (Ctrl+C to abort)\n")
                    success, output = run_tool(cmd, expanded)
                    status = "Done" if success else "Finished (non-zero exit)"
                    print(f"{output}\n\n[{status}]")
                    agent.conversation.add("user", f"/{cmd} {raw_args}")
                    agent.conversation.add("assistant", f"[Tool: {cmd} {raw_args}]\n{output}\n[{status}]")
                    continue

                # ── Security Command Center ───────────────────────────────
                elif cmd in ("security", "sec"):
                    if not SECURITY_AVAILABLE:
                        print("\n⚠️ Security Command Center not available.")
                        print("   Place security_command_center.py + port_investigator.py in Agent-Larry dir")
                    else:
                        sec_args = " ".join(args) if args else ""
                        agent.activity.emit(agent.activity.TOOL_DISPATCH, f"Security: {sec_args or 'quick'}")
                        output = _security_center.handle_command("security", sec_args)
                        print(output)
                        agent.conversation.add("user", user_input)
                        agent.conversation.add("assistant", output)
                    continue

                elif cmd in ("investigate", "ports"):
                    if not SECURITY_AVAILABLE:
                        print("\n⚠️ Security tools not available")
                    else:
                        inv_args = " ".join(args) if args else ""
                        output = _security_center.handle_command("security", f"investigate {inv_args}".strip())
                        print(output)
                        agent.conversation.add("user", user_input)
                        agent.conversation.add("assistant", output)
                    continue

                elif cmd == "hunt":
                    if not SECURITY_AVAILABLE:
                        print("\n⚠️ Security tools not available")
                    else:
                        hunt_args = " ".join(args) if args else ""
                        output = _security_center.handle_command("security", f"hunt {hunt_args}".strip())
                        print(output)
                        agent.conversation.add("user", user_input)
                        agent.conversation.add("assistant", output)
                    continue

                # ── Bash Script Runner ────────────────────────────────────
                elif cmd == "bash":
                    if not BASH_AVAILABLE:
                        print("\n⚠️ Bash Script Runner not available.")
                        print("   Place bash_script_runner.py in Agent-Larry dir")
                    else:
                        bash_args = " ".join(args) if args else ""
                        agent.activity.emit(agent.activity.TOOL_DISPATCH, f"Bash: {bash_args or 'list'}")
                        output = _bash_runner.handle_command(bash_args)
                        if output:
                            print(output)
                        agent.conversation.add("user", user_input)
                        agent.conversation.add("assistant", output or "[Bash command executed]")
                    continue

                # ── G-FORCE Extended Commands ─────────────────────────
                elif cmd == "help" or cmd == "h" or cmd == "?":
                    pending = agent.tasks.get_pending_count()
                    task_note = f" ({pending} pending)" if pending else ""
                    help_text = "\n".join([
                        "",
                        "Here's what I can do:",
                        "",
                        "  Talk to Me:                         Just type naturally — I understand.",
                        "  /robin <request>                    I'll use real tools to get it done.",
                        "  /agent <task>                       Autonomous multi-step problem solving.",
                        "",
                        f"  Tasks & Skills:{task_note}",
                        "  /task                               Manage your todo list.",
                        "  /skill                              Run a specialized skill.",
                        "",
                        "  Files:",
                        "  /ls /cd /pwd /tree                  Navigate the filesystem.",
                        "  /cat /grep /find /edit /write       Read, search, and modify files.",
                        "  /open <file>                        Open in editor with diff preview.",
                        "  /run <script>                       Execute a script.",
                        "",
                        "  Web & Research:",
                        "  /web <url>                          Scrape a page.",
                        "  /youtube <url>                      Get video transcript/summary.",
                        "  /search_web <query>                 Web search (Brave).",
                        "  /prices /headlines /ff               Finance data.",
                        "  (Or just paste a URL — I'll detect it.)",
                        "",
                        "  Security:",
                        "  /tools                              List available security tools.",
                        "  /kali <tool> [args]                 Run a Kali tool.",
                        "  /security /investigate /hunt         Security scans.",
                        "",
                        "  System:",
                        "  /models /model <name>               Switch AI models.",
                        "  /profile [name]                     Hardware profile (SPEED/ACCURACY).",
                        "  /stats /context /tokens              Usage stats.",
                        "  /mcp /github /memory                 MCP tools and integrations.",
                        "  /voice /speak /transcribe            Voice I/O.",
                        "  /sandbox                            Safe edit workflow.",
                        "",
                        "  /clear                              Fresh start (clear history).",
                        "  /quit                               See you later.",
                    ])
                    print(help_text)
                    continue

                elif cmd == "profile":
                    if args:
                        result = agent.set_profile(args[0])
                        print(f"  {result}")
                    else:
                        print(f"\n{agent.get_profile_info()}")
                    continue

                elif cmd == "context":
                    if agent.context_mgr:
                        try:
                            info = agent.context_mgr.get_stats()
                            print(f"\n📊 Context: {info}")
                        except Exception as e:
                            print(f"Context info: {e}")
                    else:
                        print(f"  History: {len(agent.conversation.history)} messages")
                        print(f"  Profile: {agent.current_profile}")
                    continue

                elif cmd == "tokens":
                    text = " ".join(args) if args else agent.conversation.get_context(n=20)
                    count = agent.count_tokens(text)
                    print(f"  Tokens: {count:,}")
                    continue

                elif cmd in ("web", "scrape"):
                    result = agent.execute_web_command("web", args)
                    print(result)
                    continue

                elif cmd == "search_web":
                    result = agent.execute_web_command("search_web", args)
                    print(result)
                    continue

                elif cmd == "youtube":
                    result = agent.execute_web_command("youtube", args)
                    print(result)
                    continue

                elif cmd == "sentiment":
                    result = agent.execute_web_command("sentiment", args)
                    print(result)
                    continue

                elif cmd == "prices":
                    result = agent.execute_web_command("prices", args)
                    print(result)
                    continue

                elif cmd == "headlines":
                    result = agent.execute_web_command("headlines", args)
                    print(result)
                    continue

                elif cmd in ("forexfactory", "ff"):
                    result = agent.execute_web_command("forexfactory", args)
                    print(result)
                    continue

                elif cmd == "voice":
                    if not VOICE_AVAILABLE or not agent.voice_manager:
                        print("❌ Voice module not available")
                        continue
                    try:
                        status = agent.voice_manager.get_status()
                    except Exception as e:
                        print(f"❌ Voice status failed: {e}")
                        continue
                    print("\n🎤 Voice Module Status:")
                    print("=" * 40)
                    print(f"🗣️ STT: {'✅' if status.get('stt_available') else '❌'} {status.get('stt_model', 'N/A')}")
                    print(f"🔊 TTS: {'✅' if status.get('tts_available') else '❌'} {status.get('tts_engine', 'N/A')}")
                    print(f"🎭 Voice Cloning: {'✅' if status.get('voice_cloning') else '❌'}")
                    print(f"📁 Voice Sample: {'✅' if status.get('voice_sample') else '❌'}")
                    tasks = status.get("voice_tasks", [])
                    print(f"🎯 Voice Tasks: {', '.join(tasks) if tasks else 'None'}")
                    continue

                elif cmd == "speak":
                    if not VOICE_AVAILABLE or not agent.voice_manager:
                        print("❌ Voice module not available")
                        continue
                    if not args:
                        print("❌ Usage: /speak <text to speak>")
                        continue
                    text = " ".join(args)
                    print(f"🎭 Generating voice for: {text[:50]}{'...' if len(text) > 50 else ''}")
                    try:
                        audio_path = agent.voice_manager.speak(text)
                        if audio_path:
                            print(f"✅ Voice generated: {audio_path}")
                            print("🎵 Playing audio...")
                            try:
                                if platform.system() == "Windows":
                                    os.startfile(audio_path)
                                elif platform.system() == "Darwin":
                                    subprocess.run(["afplay", str(audio_path)])
                                else:
                                    subprocess.run(["xdg-open", str(audio_path)])
                            except Exception as e:
                                print(f"⚠️ Could not auto-play: {e}")
                        else:
                            print("✅ Speaking...")
                    except Exception as e:
                        print(f"❌ Voice generation failed: {e}")
                    continue

                elif cmd == "listen":
                    if not VOICE_AVAILABLE or not agent.voice_manager:
                        print("❌ Voice module not available")
                        continue
                    print("🎙️ Voice input mode - speak now (press Enter when done)")
                    print("Note: This requires a microphone and audio file input")
                    print("For now, you can:")
                    print("1. Record audio to a file (WAV/MP3/OGG)")
                    print("2. Use: /transcribe <audio_file_path>")
                    continue

                elif cmd == "transcribe":
                    if not VOICE_AVAILABLE or not agent.voice_manager:
                        print("❌ Voice module not available")
                        continue
                    if not args:
                        print("❌ Usage: /transcribe <audio_file_path>")
                        continue
                    audio_path = " ".join(args)
                    if not os.path.exists(audio_path):
                        print(f"❌ Audio file not found: {audio_path}")
                        continue
                    print(f"🎤 Transcribing: {audio_path}")
                    try:
                        text = agent.voice_manager.transcribe(audio_path)
                        if text and text.strip():
                            print(f"📝 Transcribed: {text}")
                            print("\n🤖 Processing transcribed text...")
                            response = await agent.process_query(text)
                            print(f"💬 Response: {response}")
                        else:
                            print("❌ Could not transcribe audio")
                    except Exception as e:
                        print(f"❌ Transcription failed: {e}")
                    continue

                elif cmd == "sandbox":
                    if not args:
                        print("Usage: /sandbox <stage|edit|test|deploy|rollback|status> [args]")
                    else:
                        sub = args[0].lower()
                        if sub == "stage" and len(args) > 1:
                            print(agent.sandbox_stage_file(args[1]))
                        elif sub == "edit" and len(args) > 2:
                            print(agent.sandbox_edit_file(args[1], " ".join(args[2:])))
                        elif sub == "test" and len(args) > 1:
                            print(agent.sandbox_test_changes(args[1]))
                        elif sub == "deploy" and len(args) > 1:
                            print(agent.sandbox_deploy(args[1]))
                        elif sub == "rollback" and len(args) > 1:
                            print(agent.sandbox_rollback(args[1]))
                        elif sub == "status":
                            print(agent.get_sandbox_status())
                        else:
                            print("Usage: /sandbox <stage|edit|test|deploy|rollback|status> [args]")
                    continue

                elif cmd == "agent":
                    if not args:
                        print("Usage: /agent <task description>")
                    else:
                        task = " ".join(args)
                        print(f"🤖 Starting autonomous agent for: {task}")
                        def _feedback(msg):
                            print(f"  {msg}")
                        result = await agent.process_query_agentic(task, feedback_cb=_feedback)
                        print(f"\n🤖 Agent result:\n{result}")
                    continue

                elif cmd == "mcp":
                    if MCP_AVAILABLE and agent.mcp:
                        print("\n🔌 MCP Tools Status (Native — No Docker):")
                        # Show the actual servers loaded by MCPClient — this is the
                        # source of truth. Avoids hardcoded label list mismatches.
                        try:
                            loaded = sorted(agent.mcp.client.servers.keys())
                        except Exception:
                            loaded = []
                        try:
                            status = agent.mcp.get_status()
                        except Exception:
                            status = {}
                        print(f"  Servers loaded: {len(loaded)}")
                        if loaded:
                            print(f"  Names: {', '.join(loaded)}")
                        print()
                        # Known tool-wrapper categories with per-feature status
                        for key, label, note in [
                            ("filesystem",   "Filesystem",    "local sandbox r/w"),
                            ("memory",       "Memory",        "knowledge graph"),
                            ("sqlite",       "SQLite",        "data/unified_context.db"),
                            ("context7",     "Context7",      "library docs lookup"),
                            ("playwright",   "Playwright",    "headless browser"),
                            ("n8n",          "n8n",           "workflow automation"),
                            ("podman",       "Podman/Docker", "container mgmt"),
                            ("brave_search", "Brave Search",  "needs BRAVE_API_KEY in .env"),
                            ("github",       "GitHub",        "needs GITHUB_TOKEN in .env"),
                        ]:
                            ok = status.get(key, False)
                            icon = "✅" if ok else "❌"
                            print(f"  {icon} {label:<14} — {note}")
                        # Extra loaded servers not in the standard wrapper set
                        extras = [s for s in loaded if s not in {
                            "filesystem","memory","sqlite","context7","playwright",
                            "n8n","podman","brave-search","github",
                        }]
                        if extras:
                            print()
                            print(f"  Also loaded: {', '.join(extras)}")
                    else:
                        print("❌ MCP tools not available — check mcp.json and mcp_servers/ package")
                    continue

                elif cmd in ("rag", "ask"):
                    if not args:
                        print("❌ Usage: /rag <question>")
                    else:
                        rag_query = " ".join(args)
                        print(agent.ask_about_code(rag_query))
                    continue

                elif cmd == "summarize":
                    if CONTEXT_MANAGER_AVAILABLE and agent.context_mgr:
                        print("📝 Forcing context summarization...")
                        try:
                            summary = agent.context_mgr.force_summarize()
                            if summary:
                                print(f"✅ Context summarized ({len(summary)} chars)")
                                try:
                                    stats = agent.context_mgr.get_stats()
                                    print(f"   New token usage: {stats.get('current_tokens', 0):,} / {stats.get('max_tokens', 0):,}")
                                except Exception:
                                    pass
                            else:
                                print("⚠️ No messages to summarize")
                        except Exception as e:
                            print(f"❌ Summarization failed: {e}")
                    else:
                        print("❌ Context manager not available")
                    continue

                elif cmd == "sessions":
                    if CONTEXT_MANAGER_AVAILABLE and agent.context_mgr:
                        if args and args[0] == "new":
                            try:
                                new_id = agent.context_mgr.new_session()
                                print(f"✅ New session: {str(new_id)[:8]}...")
                            except Exception as e:
                                print(f"❌ Could not create session: {e}")
                        else:
                            try:
                                sessions = agent.context_mgr.list_sessions()
                                current = getattr(agent.context_mgr, 'current_session', None)
                                print("\n📋 Sessions:")
                                for sess in sessions:
                                    sid = sess.get("id", "?")
                                    marker = "→" if sid == current else " "
                                    print(f"  {marker} {str(sid)[:8]}... ({sess.get('messages', 0)} msgs, {sess.get('tokens', 0):,} tokens)")
                                print("\n   Use /sessions new to start a new session")
                            except Exception as e:
                                print(f"❌ Could not list sessions: {e}")
                    else:
                        print("❌ Context manager not available")
                    continue

                elif cmd == "mappings":
                    if CONTEXT_MANAGER_AVAILABLE and agent.task_mgr:
                        print("\n  Task → Model Mappings:")
                        try:
                            for task, model in agent.task_mgr.task_models.items():
                                print(f"    {str(task).ljust(12)} → {model}")
                        except Exception as e:
                            print(f"  Could not read mappings: {e}")
                    else:
                        print("  Model task manager not available.")
                    continue

                elif cmd == "scrape":
                    if not args:
                        print("❌ Usage: /scrape <url>")
                    elif not WEB_TOOLS_AVAILABLE or not agent.web_scraper:
                        print("❌ Web scraper not available")
                    else:
                        url = args[0]
                        print(f"🌐 Scraping: {url}")
                        try:
                            if hasattr(agent.web_scraper, 'scrape_and_save'):
                                filepath, success = agent.web_scraper.scrape_and_save(url)
                            else:
                                content, filepath, success = agent.web_scraper.scrape_to_markdown(url)
                            if success:
                                print(f"✅ Saved to: {filepath}")
                                if agent.rag_manager:
                                    try:
                                        content_text = Path(filepath).read_text(encoding="utf-8")
                                        agent.rag_manager.store_document(
                                            content_text[:5000],
                                            metadata={"source": "web_content", "url": url}
                                        )
                                        print("📚 Added to RAG memory")
                                    except Exception:
                                        pass
                            else:
                                print(f"❌ Error: {filepath}")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    continue

                elif cmd in ("youtube", "yt"):
                    if not args:
                        print("❌ Usage: /youtube <url>")
                        continue
                    if not WEB_TOOLS_AVAILABLE:
                        print("❌ YouTube tools not available")
                        continue
                    url = args[0]
                    print(f"📺 Processing YouTube: {url}")
                    try:
                        # Re-initialize the summarizer to clear old cache
                        from web_tools import YouTubeSummarizer
                        yt = YouTubeSummarizer(
                            output_dir=str(BASE_DIR / "exports"),
                            chroma_db_path=str(BASE_DIR / "chroma_db"),
                        )
                        summary = yt.get_video_summary(url)
                        if summary:
                            print(f"\n📝 Summary:\n{summary}")
                            agent.conversation.add(
                                "user",
                                f"I just watched this YouTube video ({url}). Here is the summary:\n{summary}",
                            )
                            agent.conversation.add(
                                "assistant", "Got it. I've analyzed the video summary."
                            )
                            try:
                                yt.process_video(url)
                                print("✅ Full transcript indexed and saved to knowledge base.")
                            except Exception:
                                pass
                        else:
                            print("❌ Could not generate summary.")
                    except Exception as e:
                        print(f"❌ YouTube Error: {e}")
                    continue

                elif cmd == "memory":
                    if not MCP_AVAILABLE or not agent.mcp or not getattr(agent.mcp, 'memory', None) or not getattr(agent.mcp.memory, 'available', False):
                        print("❌ Memory server not available")
                        continue
                    if not args:
                        print("\n🧠 Memory Commands:")
                        print("  /memory show               - Show knowledge graph stats")
                        print("  /memory search <query>     - Search entities")
                        print("  /memory add <name> <type>  - Add an entity")
                        print("  /memory observe <name> <observation> - Add observation")
                        continue
                    subcmd = args[0].lower()
                    subargs = args[1:]
                    try:
                        if subcmd == "show":
                            graph = agent.mcp.memory.read_graph()
                            print(f"\n🧠 Knowledge Graph:")
                            print(f"  Entities: {graph.get('entity_count', 0)}")
                            print(f"  Relations: {graph.get('relation_count', 0)}")
                            if graph.get("entities"):
                                print("\n  Entities:")
                                for e in graph["entities"][:10]:
                                    print(f"    • {e['name']} [{e['entity_type']}] - {len(e.get('observations', []))} observations")
                        elif subcmd == "search" and subargs:
                            mem_query = " ".join(subargs)
                            result = agent.mcp.memory.search_nodes(mem_query)
                            print(f"\n🔍 Search results for '{mem_query}':")
                            for e in result.get("results", []):
                                print(f"  • {e['name']} [{e['entity_type']}]")
                                for obs in e.get("observations", [])[:2]:
                                    print(f"      - {obs[:80]}...")
                        elif subcmd == "add" and len(subargs) >= 2:
                            name = subargs[0]
                            entity_type = subargs[1]
                            agent.mcp.memory.create_entities(
                                [{"name": name, "entityType": entity_type, "observations": []}]
                            )
                            print(f"✅ Created entity: {name} [{entity_type}]")
                        elif subcmd == "observe" and len(subargs) >= 2:
                            name = subargs[0]
                            observation = " ".join(subargs[1:])
                            agent.mcp.memory.add_observations(
                                [{"entityName": name, "contents": [observation]}]
                            )
                            print(f"✅ Added observation to {name}")
                        else:
                            print("❌ Unknown memory command. Use /memory for help.")
                    except Exception as e:
                        print(f"❌ Memory command failed: {e}")
                    continue

                elif cmd in ("github", "gh"):
                    if not MCP_AVAILABLE or not agent.mcp or not getattr(agent.mcp, 'github', None):
                        print("❌ GitHub MCP tools not available")
                        continue
                    if not args:
                        print("\n🐙 GitHub Commands:")
                        print("  /github auth               - Check GitHub authentication")
                        print("  /github repos              - List your repositories")
                        print("  /github repo <owner/name>  - Get repository details")
                        print("  /github issues <owner/name> [state] - List issues (open/closed/all)")
                        print("  /github prs <owner/name> [state]    - List pull requests")
                        print("  /github search <query>     - Search code in GitHub")
                        continue
                    subcmd = args[0].lower()
                    subargs = args[1:]
                    try:
                        if subcmd == "auth":
                            print("🔑 Checking GitHub authentication...")
                            user = agent.mcp.github.get_user()
                            if "error" in user:
                                print(f"❌ Authentication failed: {user['error']}")
                                print("\n💡 To fix: Generate a new Personal Access Token at:")
                                print("   https://github.com/settings/tokens")
                                print("   Then update GITHUB_TOKEN in mcp.json or .env")
                            else:
                                print(f"✅ Authenticated as: {user.get('login')}")
                                print(f"   Name: {user.get('name', 'N/A')}")
                                print(f"   Public repos: {user.get('public_repos', 0)}")
                        elif subcmd == "repos":
                            print("📦 Fetching repositories...")
                            repos = agent.mcp.github.list_repos()
                            if isinstance(repos, dict) and "error" in repos:
                                print(f"❌ {repos['error']}")
                            elif repos:
                                print(f"\n📦 Your Repositories ({len(repos)}):")
                                for repo in repos[:20]:
                                    stars = repo.get("stargazers_count", 0)
                                    lang = repo.get("language", "N/A")
                                    print(f"  • {repo['full_name']} ⭐{stars} [{lang}]")
                                if len(repos) > 20:
                                    print(f"  ... and {len(repos) - 20} more")
                            else:
                                print("❌ No repositories found or authentication failed")
                        elif subcmd == "repo" and subargs:
                            repo_name = subargs[0]
                            print(f"📦 Fetching {repo_name}...")
                            repo = agent.mcp.github.get_repo(repo_name)
                            if "error" in repo:
                                print(f"❌ {repo['error']}")
                            elif repo:
                                print(f"\n📦 {repo['full_name']}")
                                print(f"  Description: {repo.get('description', 'N/A')}")
                                print(f"  Language: {repo.get('language', 'N/A')}")
                                print(f"  Stars: {repo.get('stargazers_count', 0)}")
                                print(f"  Forks: {repo.get('forks_count', 0)}")
                                print(f"  Open Issues: {repo.get('open_issues_count', 0)}")
                                print(f"  URL: {repo.get('html_url', 'N/A')}")
                            else:
                                print(f"❌ Repository not found: {repo_name}")
                        elif subcmd == "issues" and subargs:
                            repo_name = subargs[0]
                            state = subargs[1] if len(subargs) > 1 else "open"
                            print(f"📋 Fetching issues for {repo_name}...")
                            issues = agent.mcp.github.list_issues(repo_name, state=state)
                            if issues:
                                print(f"\n📋 Issues ({state}) - {len(issues)} found:")
                                for issue in issues[:15]:
                                    labels = ", ".join([l["name"] for l in issue.get("labels", [])])
                                    print(f"  #{issue['number']} {issue['title'][:60]}")
                                    if labels:
                                        print(f"       Labels: {labels}")
                            else:
                                print(f"No {state} issues found")
                        elif subcmd == "prs" and subargs:
                            repo_name = subargs[0]
                            state = subargs[1] if len(subargs) > 1 else "open"
                            print(f"🔀 Fetching PRs for {repo_name}...")
                            prs = agent.mcp.github.list_pull_requests(repo_name, state=state)
                            if prs:
                                print(f"\n🔀 Pull Requests ({state}) - {len(prs)} found:")
                                for pr in prs[:15]:
                                    print(f"  #{pr['number']} {pr['title'][:60]}")
                                    print(f"       By: {pr['user']['login']} | {pr['state']}")
                            else:
                                print(f"No {state} pull requests found")
                        elif subcmd == "search" and subargs:
                            gh_query = " ".join(subargs)
                            print(f"🔍 Searching GitHub for: {gh_query}...")
                            results = agent.mcp.github.search_code(gh_query)
                            if results:
                                print(f"\n🔍 Search Results ({len(results)} found):")
                                for item in results[:10]:
                                    print(f"  • {item['repository']['full_name']}/{item['name']}")
                                    print(f"    {item['html_url']}")
                            else:
                                print("No results found")
                        else:
                            print("❌ Unknown GitHub command. Use /github for help.")
                    except Exception as e:
                        print(f"❌ GitHub command failed: {e}")
                    continue

                elif cmd == "docker":
                    print("\n🐳 Docker commands disabled - using native MCP servers")
                    print("  Native tools available (no Docker required):")
                    print("  • /mcp          - Show all MCP tools status")
                    print("  • /search_web   - Web search via Brave API")
                    print("  • /memory       - Knowledge graph storage")
                    print("  • /github       - GitHub API operations")
                    continue

                elif cmd == "search":
                    if not args:
                        print("Usage: /search <query>")
                    elif agent.rag:
                        query = " ".join(args)
                        hits = agent.rag.hybrid_search(query, k=10, final_k=5)
                        for i, h in enumerate(hits):
                            score = h.get('rerank_score', h.get('score', 0))
                            src = h.get('metadata', {}).get('source', '?')
                            print(f"  [{i+1}] ({score:.2f}) {src}")
                            print(f"      {h['content'][:150]}...")
                    else:
                        print("  RAG not available")
                    continue

                elif cmd == "run":
                    if not args:
                        print("Usage: /run <script.py>")
                    else:
                        script = args[0]
                        print(f"Running: {script}")
                        try:
                            r = subprocess.run(
                                [sys.executable, script] if script.endswith('.py') else [script],
                                capture_output=True, text=True, timeout=300, cwd=str(BASE_DIR)
                            )
                            if r.stdout:
                                print(r.stdout[:4000])
                            if r.stderr:
                                print(f"STDERR:\n{r.stderr[:2000]}")
                            print(f"[Exit code: {r.returncode}]")
                        except subprocess.TimeoutExpired:
                            print("Script timed out (300s)")
                        except Exception as e:
                            print(f"Error: {e}")
                    continue

                elif cmd == "skill":
                    if not agent.skill_manager:
                        print("  Skill Manager not available")
                        continue
                    if not args:
                        print("\n🧰 Skills:")
                        for cat in agent.skill_manager.get_categories():
                            cat_skills = agent.skill_manager.get_skills_by_category(cat)
                            executable = [s for s in cat_skills if s.function]
                            if executable:
                                print(f"\n  {cat.upper()}:")
                                for s in executable:
                                    print(f"    /skill {s.name} — {s.description}")
                        print(f"\n  Run a skill: /skill <name> [args]")
                        stats = agent.skill_manager.get_skill_stats()
                        print(f"  Total: {stats['total_skills']} skills, {stats['enabled_skills']} enabled, {stats['total_executions']} runs")
                    elif args[0] == "help" and len(args) > 1:
                        skill = agent.skill_manager.get_skill(args[1])
                        if skill:
                            print(f"\n  {skill.name} — {skill.description}")
                            if skill.parameters:
                                print(f"  Parameters: {skill.parameters}")
                            if skill.examples:
                                print(f"  Examples: {', '.join(skill.examples)}")
                        else:
                            print(f"  No skill named '{args[1]}'")
                    else:
                        skill_name = args[0]
                        skill_args = " ".join(args[1:]) if len(args) > 1 else ""
                        skill = agent.skill_manager.get_skill(skill_name)
                        if not skill:
                            print(f"  No skill named '{skill_name}'. Try /skill to see available ones.")
                        elif not skill.function:
                            print(f"  '{skill_name}' exists but has no implementation yet.")
                        else:
                            print(f"  Running {skill_name}...")
                            kwargs = {"filepath": skill_args} if skill_args else {}
                            result = agent.skill_manager.execute_skill(skill_name, **kwargs)
                            if result.get("success"):
                                print(f"\n{result['result']}")
                            else:
                                print(f"  Error: {result.get('error', 'unknown')}")
                    continue

                elif cmd == "robin":
                    if not args:
                        print("Tell Robin what to do: /robin <your request>")
                        print("Start fresh with: /robin new <request>")
                        continue
                    new_task = False
                    if args[0].lower() == "new":
                        new_task = True
                        args = args[1:]
                    if not args:
                        print("What should Robin do?")
                        continue
                    message = " ".join(args)
                    response = agent.process_tool_query(message, new_task=new_task)
                    print(f"\n🦜 Robin:\n{response}")
                    continue

                elif cmd in ("task", "tasks", "todo"):
                    if not args:
                        pending = agent.tasks.get_pending_count()
                        print(f"\n📋 Tasks ({pending} pending):")
                        print(agent.tasks.list_tasks())
                        print("\n  /task add <title>       — add a new task")
                        print("  /task done <id>         — mark as complete")
                        print("  /task rm <id>           — remove a task")
                        print("  /task all               — show completed too")
                        print("  /task high <title>      — add high-priority task")
                        continue
                    sub = args[0].lower()
                    if sub == "add" and len(args) > 1:
                        title = " ".join(args[1:])
                        t = agent.tasks.add(title)
                        print(f"  Added #{t['id']}: {t['title']}")
                    elif sub == "high" and len(args) > 1:
                        title = " ".join(args[1:])
                        t = agent.tasks.add(title, priority="high")
                        print(f"  🔴 Added high-priority #{t['id']}: {t['title']}")
                    elif sub == "done" and len(args) > 1:
                        try:
                            tid = int(args[1])
                            t = agent.tasks.complete(tid)
                            if t:
                                print(f"  ✅ #{tid} done: {t['title']}")
                            else:
                                print(f"  Task #{tid} not found.")
                        except ValueError:
                            print("  Need a task number: /task done <id>")
                    elif sub in ("rm", "remove", "delete") and len(args) > 1:
                        try:
                            tid = int(args[1])
                            if agent.tasks.remove(tid):
                                print(f"  Removed task #{tid}")
                            else:
                                print(f"  Task #{tid} not found.")
                        except ValueError:
                            print("  Need a task number: /task rm <id>")
                    elif sub == "all":
                        print(f"\n📋 All Tasks:")
                        print(agent.tasks.list_tasks(show_done=True))
                    else:
                        # Treat unknown subcommand as a task title
                        title = " ".join(args)
                        t = agent.tasks.add(title)
                        print(f"  Added #{t['id']}: {t['title']}")
                    continue

                else:
                    # Check if it's close to a real command (fuzzy help)
                    known = ["help","quit","models","model","stats","clear","history",
                             "profile","task","skill","robin","agent","mcp","tools",
                             "kali","security","web","youtube","github","memory"]
                    close = [k for k in known if k.startswith(cmd[:2])]
                    if close:
                        print(f"  I don't know /{cmd}. Did you mean: {', '.join('/'+c for c in close[:3])}?")
                    else:
                        print(f"  Unknown command /{cmd}. Type /help to see what I can do.")
                    continue

            # Auto-detect URLs
            if user_input.startswith("http://") or user_input.startswith("https://"):
                if "youtube.com" in user_input or "youtu.be" in user_input:
                    if agent.youtube:
                        print("📺 YouTube URL detected — fetching transcript...")
                        result = agent.execute_web_command("youtube", [user_input])
                        print(result[:4000])
                        continue
                elif agent.web_scraper:
                    print("🌐 URL detected — scraping...")
                    result = agent.execute_web_command("web", [user_input])
                    print(result[:4000])
                    continue

            # Auto-route operational requests to the Robin tool-calling loop.
            # Triggers on execution verbs or scheduling intent so things like
            # "start the pipeline" or "schedule a health check every 60s" get
            # real tool calls instead of narrated chat.
            if AGENT_TOOLS_AVAILABLE:
                _low = user_input.lower()
                _op_phrases = (
                    "run script", "run the script", "execute script",
                    "start background", "start the pipeline", "start pipeline",
                    "stop background", "kill background", "kill job",
                    "schedule a", "schedule interval", "schedule health",
                    "health check", "health-check",
                    "list jobs", "list scheduled", "remove scheduled",
                )
                if any(p in _low for p in _op_phrases):
                    print()
                    response = agent.process_tool_query(user_input)
                    print(f"\n🦜 Robin:\n{response}")
                    continue

            # Process query
            print()
            response = await agent.process_query(user_input)
            # Wrap long lines for terminal display
            import textwrap
            terminal_width = shutil.get_terminal_size(fallback=(100, 24)).columns
            wrapped = []
            for line in response.splitlines():
                if len(line) > terminal_width:
                    wrapped.extend(textwrap.wrap(line, width=terminal_width - 2) or [""])
                else:
                    wrapped.append(line)
            print(f"\n🤖 Larry:\n" + "\n".join(wrapped))
            
        except KeyboardInterrupt:
            if readline:
                readline.write_history_file(history_file)
            _disable_bracketed_paste()
            print("\n👋 Goodbye!")
            break
        except EOFError:
            if readline:
                readline.write_history_file(history_file)
            _disable_bracketed_paste()
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
