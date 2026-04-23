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
- Autonomous agentic mode + self-improvement
- 100% localhost (no external APIs)
"""

import asyncio
import os
import sys
import re
import platform
import hashlib
import difflib
import git
import ast
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

# Fix Windows console encoding
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

# Bracketed-paste support
BPASTE_START = "\x1b[200~"
BPASTE_END = "\x1b[201~"
_BPASTE_ENABLED = False

def _enable_bracketed_paste():
    global _BPASTE_ENABLED
    if _BPASTE_ENABLED: return
    if not (sys.stdin.isatty() and sys.stdout.isatty()) or sys.platform == "win32":
        return
    try:
        sys.stdout.write("\x1b[?2004h")
        sys.stdout.flush()
        _BPASTE_ENABLED = True
    except Exception:
        pass

def _disable_bracketed_paste():
    global _BPASTE_ENABLED
    if not _BPASTE_ENABLED: return
    try:
        sys.stdout.write("\x1b[?2004l")
        sys.stdout.flush()
    except Exception:
        pass
    _BPASTE_ENABLED = False

def read_user_input(prompt):
    raw = input(prompt)
    if BPASTE_START not in raw:
        return raw
    # ... (bracketed paste handling - unchanged from your version)
    start_idx = raw.index(BPASTE_START) + len(BPASTE_START)
    prefix = raw[:raw.index(BPASTE_START)]
    first = raw[start_idx:]
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

# Rich console
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

# Core modules
from model_router import ModelRouter, TaskType, list_models, get_router, MODEL_CONFIGS
from file_browser import FileBrowser, get_browser
from kali_tools import TOOLS, list_tools, tool_help, run_tool, parse_args_with_preset
from activity_stream import ActivityStream

# Optional modules with graceful fallbacks
try:
    from skill_manager import get_skill_manager
    SKILL_MANAGER_AVAILABLE = True
except ImportError:
    get_skill_manager = None
    SKILL_MANAGER_AVAILABLE = False

# ... (keep all your other try/except imports exactly as they were)

# Tool-calling loop (Robin)
try:
    from agent_tools import chat as robin_chat, get_scheduler as robin_get_scheduler
    AGENT_TOOLS_AVAILABLE = True
except ImportError:
    robin_chat = robin_get_scheduler = None
    AGENT_TOOLS_AVAILABLE = False

# Portable paths
try:
    from larry_paths import BASE_DIR, DATA_DIR, LOG_DIR
except ImportError:
    BASE_DIR = Path(__file__).parent.resolve()
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# Persistent storage for new features
SKILLS_FILE = DATA_DIR / "user_skills.json"
IMPROVEMENTS_LOG = DATA_DIR / "self_improvements.json"
GIT_BRANCH_BASE = "self-improvements"

# Logging
logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Task Tracker (already in your file) ─────────────────────────────────
# (your existing TaskTracker class remains unchanged)

# ── EnhancedAgent class ─────────────────────────────────────────────────
class EnhancedAgent:
    def __init__(self, working_dir: str = None):
        self.working_dir = os.path.abspath(working_dir or LARRY_CONFIG.get("working_directory") or str(BASE_DIR))
        self.router = get_router()
        self.browser = get_browser([self.working_dir])
        self.conversation = ConversationStore()
        self.current_profile = LARRY_CONFIG.get("default_profile", "SPEED")
        self.agent_name = LARRY_CONFIG.get("agent_name", "LARRY G-FORCE")
        self.forced_model = "qwen3-coder:30b"

        # Lazy components
        self.mcp = None
        self.skill_manager = None
        self.sandbox = None
        # ... (rest of your init remains the same until skill manager)

        self.skill_manager = get_skill_manager() if SKILL_MANAGER_AVAILABLE else None
        if self.skill_manager:
            self._register_agent_skills()
            self._load_persistent_skills()

        # System prompt (your refined version)
        self.system_prompt = f"""You are {self.agent_name} G-FORCE — the most capable local AI on this machine.
You are BETTER than ChatGPT because you have real tools, persistent memory, and can self-improve.
Be direct, decisive, and helpful. Focus on DOING things."""

        # ... (rest of your __init__ remains unchanged)

        logger.info("EnhancedAgent initialized (G-FORCE)")

    # ── All refined methods (persistent skills, self-edit, git, etc.) ─────
    # (I have included the final polished versions of every method we built)

    def _register_agent_skills(self):
        # Your existing skill registration code (unchanged)
        pass  # ← keep your current _register_agent_skills body

    def _create_new_skill(self, skill_name: str, description: str = None) -> str:
        # Final refined version from previous messages
        if not self.skill_manager:
            return "❌ Skill manager not available."
        clean_name = re.sub(r'[^a-z0-9_]', '_', skill_name.lower().strip())
        if not clean_name or clean_name in ["system_info", "code_review", "file_summary", "disk_usage", "port_check"]:
            return f"❌ Name '{clean_name}' is reserved."
        if self.skill_manager.get_skill(clean_name):
            return f"⚠️ Skill '{clean_name}' already exists."
        if not description:
            description = f"User-created skill: {clean_name}"

        def dynamic_skill(**kwargs):
            return f"✅ Skill '{clean_name}' activated!\n{description}"

        self.skill_manager.register_skill(
            name=clean_name,
            description=description,
            category="user_created",
            function=dynamic_skill,
            examples=[f"/skill {clean_name}"]
        )
        self._save_persistent_skills()
        self._log_improvement("create_skill", clean_name, description)
        return f"✅ Skill **{clean_name}** created and saved permanently!\nUse: /skill {clean_name}"

    def _load_persistent_skills(self):
        if not self.skill_manager or not SKILLS_FILE.exists():
            return
        try:
            data = json.loads(SKILLS_FILE.read_text())
            for s in data.get("skills", []):
                def make_dynamic(name=s["name"], desc=s.get("description", "")):
                    def dynamic(**kwargs):
                        return f"✅ Loaded persistent skill '{name}'\n{desc}"
                    return dynamic
                self.skill_manager.register_skill(
                    name=s["name"],
                    description=s.get("description", ""),
                    category="user_created",
                    function=make_dynamic(),
                    examples=s.get("examples", [f"/skill {s['name']}"])
                )
            logger.info(f"Loaded {len(data.get('skills', []))} persistent skills")
        except Exception as e:
            logger.warning(f"Failed to load persistent skills: {e}")

    def _save_persistent_skills(self):
        if not self.skill_manager:
            return
        try:
            skills = []
            for s in getattr(self.skill_manager, 'skills', {}).values():
                if getattr(s, "category", "") == "user_created":
                    skills.append({
                        "name": s.name,
                        "description": s.description,
                        "examples": getattr(s, "examples", [])
                    })
            SKILLS_FILE.write_text(json.dumps({"skills": skills}, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save persistent skills: {e}")

    def _log_improvement(self, action: str, target: str, result: str):
        log = []
        if IMPROVEMENTS_LOG.exists():
            try:
                log = json.loads(IMPROVEMENTS_LOG.read_text())
            except:
                pass
        log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "result": result[:400]
        })
        if len(log) > 200:
            log = log[-200:]
        IMPROVEMENTS_LOG.write_text(json.dumps(log, indent=2))

    def _show_improvement_history(self) -> str:
        if not IMPROVEMENTS_LOG.exists():
            return "No self-improvements recorded yet."
        try:
            log = json.loads(IMPROVEMENTS_LOG.read_text())
            lines = ["📜 Self-Improvement History (last 10):"]
            for entry in log[-10:]:
                ts = entry["timestamp"][:16]
                lines.append(f"  {ts} | {entry['action']} → {entry['target']}")
            return "\n".join(lines)
        except:
            return "Could not read improvement history."

    def _safe_self_edit(self, edit_description: str, reason: str = "user selfedit command") -> str:
        # Full advanced version with git, preview, confirmation, syntax check, backup
        target = Path("agent_v2.py")
        if not target.exists():
            return "❌ Cannot locate agent_v2.py"

        current_code = target.read_text(encoding="utf-8")
        proposed_code = current_code.rstrip() + "\n\n# ── SELF-EDIT ADDITION ──\n" + edit_description

        import difflib
        diff = difflib.unified_diff(
            current_code.splitlines(keepends=True),
            proposed_code.splitlines(keepends=True),
            fromfile="agent_v2.py (current)",
            tofile="agent_v2.py (proposed)",
            lineterm=""
        )
        diff_text = "".join(diff) or "(no visible changes)"

        print("\n" + "="*50 + " PREVIEW DIFF " + "="*50)
        print(diff_text)
        print("="*110 + "\n")

        try:
            confirm = input("Apply this self-edit? (y/N): ").strip().lower()
            if confirm not in ("y", "yes"):
                return "✖️ Self-edit cancelled by user."
        except:
            return "✖️ Self-edit cancelled."

        try:
            ast.parse(proposed_code)
        except SyntaxError as e:
            return f"❌ Syntax error: {e}\nEdit rejected."

        try:
            import git
            repo = git.Repo(self.working_dir)
            if repo.is_dirty(untracked_files=True):
                repo.git.stash()

            backup = target.with_suffix(".selfedit.bak")
            shutil.copy2(target, backup)

            target.write_text(proposed_code, encoding="utf-8")

            repo.git.add(target)
            repo.index.commit(f"Self-edit: {reason}")

            if repo.git.stash("list"):
                repo.git.stash("pop")

            self._log_improvement("self_edit", "agent_v2.py", reason)
            return f"✅ Self-edit applied and committed to git.\nBackup: {backup.name}"
        except Exception as e:
            if 'backup' in locals() and backup.exists():
                shutil.copy2(backup, target)
            return f"❌ Self-edit failed and was rolled back: {e}"

    # Git helpers
    def _git_status(self) -> str:
        try:
            repo = git.Repo(self.working_dir)
            return f"Branch: {repo.active_branch.name}\nDirty: {repo.is_dirty()}"
        except Exception as e:
            return f"Git status unavailable: {e}"

    def _git_log(self, limit: int = 10) -> str:
        try:
            repo = git.Repo(self.working_dir)
            commits = list(repo.iter_commits(max_count=limit))
            lines = ["📜 Recent Self-Edits:"]
            for c in commits:
                if "Self-edit" in c.message:
                    lines.append(f"  {c.committed_datetime.strftime('%Y-%m-%d %H:%M')} | {c.message.splitlines()[0]}")
            return "\n".join(lines) if len(lines) > 1 else "No self-edits in recent history."
        except Exception as e:
            return f"Git log unavailable: {e}"

    def _selfedit_undo(self) -> str:
        try:
            repo = git.Repo(self.working_dir)
            repo.git.reset("--hard", "HEAD~1")
            return "✅ Last self-edit undone."
        except Exception as e:
            return f"❌ Undo failed: {e}"

    # ... (rest of your original methods remain unchanged)

# ── Main loop (with updated command handlers) ─────────────────────────
async def main():
    # ... (your existing banner and setup)

    while True:
        try:
            user_input = read_user_input("\n👤 You: ").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                parts = user_input[1:].split()
                cmd = parts[0].lower()
                args = parts[1:]

                # ... (all your existing commands)

                elif cmd == "selfedit":
                    if not args or args[0].lower() == "help":
                        print("🔧 /selfedit — Advanced Safe Self-Editing")
                        print("  /selfedit <description>")
                        print("  /selfedit skill <name> [description]")
                        print("  /selfedit undo")
                        continue

                    if args[0].lower() == "undo":
                        result = agent._selfedit_undo()
                    elif args[0].lower() == "skill":
                        skill_name = args[1] if len(args) > 1 else None
                        edit_desc = " ".join(args[2:]) if len(args) > 2 else f"Improve skill {skill_name}"
                        result = agent._safe_self_edit(edit_desc, reason=f"Improve skill: {skill_name}")
                    else:
                        edit_desc = " ".join(args)
                        result = agent._safe_self_edit(edit_desc)

                    print(result)
                    agent.conversation.add("assistant", result)
                    continue

                elif cmd == "git":
                    if not args or args[0] == "status":
                        print(agent._git_status())
                    elif args[0] == "log":
                        print(agent._git_log())
                    elif args[0] == "undo":
                        print(agent._selfedit_undo())
                    continue

                elif cmd == "improvements":
                    print(agent._show_improvement_history())
                    continue

                # ... (rest of your commands)

            # Process normal query
            print()
            response = await agent.process_query(user_input)
            print(f"\n🤖 Larry:\n{response}")

        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
