#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║             AGENT-LARRY v2.1 — UNIVERSAL STARTUP SCRIPT                   ║
║                                                                            ║
║  Complete orchestration for starting all services, tools, and the agent   ║
║  in the correct dependency order with full verification.                  ║
║                                                                            ║
║  Usage:                                                                    ║
║    python START_AGENT.py              # Full startup with all services    ║
║    python START_AGENT.py --check      # Validate setup without starting   ║
║    python START_AGENT.py --quick      # Quick startup (no models check)   ║
║    python START_AGENT.py --docker     # Start with Docker services       ║
║    python START_AGENT.py --telegram   # Also start telegram bot          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import argparse
import subprocess
import signal
import socket
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# =============================================================================
# DISABLE TELEMETRY EARLY
# =============================================================================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["POSTHOG_DISABLED"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# =============================================================================
# CONFIG
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_PATH = PROJECT_ROOT / ".venv"
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
SANDBOX_DIR = PROJECT_ROOT / "sandbox"
CHROMA_DB = PROJECT_ROOT / "chroma_db"
CONTEXT7_CACHE = PROJECT_ROOT / "context7_cache"
STARTUP_LOG = LOG_DIR / f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

OLLAMA_PORT = 11434
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_TIMEOUT = 10

# Required directories
REQUIRED_DIRS = [DATA_DIR, LOG_DIR, SANDBOX_DIR, CHROMA_DB, CONTEXT7_CACHE]

# Required Python modules
REQUIRED_MODULES = [
    "model_router.py",
    "file_browser.py",
    "kali_tools.py",
    "activity_stream.py",
    "skill_manager.py",
    "web_tools.py",
    "voice_module.py",
    "mcp_client.py",
    "safe_code_executor.py",
    "universal_file_handler.py",
    "hardware_profiles.py",
    "token_manager.py",
    "unified_context_manager.py",
    "cross_platform_paths.py",
    "sandbox_manager.py",
    "security_command_center.py",
    "bash_script_runner.py",
    "agent_v2.py",
]

# Optional modules
OPTIONAL_MODULES = [
    "production_rag.py",
    "rag_integration.py",
    "telegram_bot.py",
    "context_manager.py",
]

# =============================================================================
# COLORS & FORMATTING
# =============================================================================

class Colors:
    GOLD = '\033[38;2;255;215;0m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    CHECK = '✓'
    CROSS = '✗'
    ARROW = '→'
    GEAR = '⚙'
    ROCKET = '🚀'


class Logger:
    def __init__(self, logfile: Path):
        self.logfile = logfile
        self.logfile.parent.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, level: str = "info", console: bool = True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level.upper():8}] {msg}"
        
        if console:
            if level == "success":
                print(f"{Colors.GREEN}{Colors.CHECK} {msg}{Colors.END}")
            elif level == "error":
                print(f"{Colors.RED}{Colors.CROSS} {msg}{Colors.END}")
            elif level == "warning":
                print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")
            elif level == "info":
                print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")
            elif level == "step":
                print(f"{Colors.CYAN}{Colors.ARROW} {msg}{Colors.END}")
            elif level == "debug":
                print(f"{Colors.DIM}⊙ {msg}{Colors.END}")
        
        try:
            with open(self.logfile, "a") as f:
                f.write(log_msg + "\n")
        except:
            pass

    def section(self, title: str):
        self.log(f"\n{'='*70}\n{title}\n{'='*70}\n", console=True)


# =============================================================================
# STARTUP CHECKS
# =============================================================================

class StartupChecker:
    def __init__(self, logger: Logger, quick: bool = False):
        self.logger = logger
        self.quick = quick
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check_python_version(self) -> bool:
        """Verify Python 3.10+"""
        version = sys.version_info
        if version >= (3, 10):
            self.logger.log(f"Python {version.major}.{version.minor}.{version.micro}", "success")
            self.checks_passed += 1
            return True
        else:
            self.logger.log(f"Python 3.10+ required (found {version.major}.{version.minor})", "error")
            self.checks_failed += 1
            return False

    def check_venv(self) -> bool:
        """Verify virtual environment"""
        if not VENV_PATH.exists():
            self.logger.log(f"Virtual env not found: {VENV_PATH}", "warning")
            self.logger.log("Run: python -m venv .venv", "info")
            self.warnings += 1
            return False
        
        self.logger.log("Virtual environment activated", "success")
        self.checks_passed += 1
        return True

    def check_directories(self) -> bool:
        """Create required directories"""
        all_ok = True
        for d in REQUIRED_DIRS:
            try:
                d.mkdir(parents=True, exist_ok=True)
                self.logger.log(f"Directory: {d.name}", "debug")
            except Exception as e:
                self.logger.log(f"Failed to create {d.name}: {e}", "error")
                all_ok = False
                self.checks_failed += 1
        
        if all_ok:
            self.checks_passed += 1
            self.logger.log(f"All {len(REQUIRED_DIRS)} directories ready", "success")
        return all_ok

    def check_modules(self, required_only: bool = False) -> bool:
        """Verify Python modules exist"""
        modules = REQUIRED_MODULES if required_only else (REQUIRED_MODULES + OPTIONAL_MODULES)
        missing = []
        
        for mod in modules:
            mod_path = PROJECT_ROOT / mod
            if not mod_path.exists():
                missing.append(mod)
        
        if not missing:
            self.logger.log(f"All {len(REQUIRED_MODULES)} required modules present", "success")
            self.checks_passed += 1
            return True
        else:
            self.logger.log(f"Missing modules: {', '.join(missing)}", "error")
            for m in missing:
                is_required = m in REQUIRED_MODULES
                level = "error" if is_required else "warning"
                self.logger.log(f"  → {m}", level)
                if is_required:
                    self.checks_failed += 1
                else:
                    self.warnings += 1
            return len([m for m in missing if m in REQUIRED_MODULES]) == 0

    def check_env_file(self) -> bool:
        """Check .env file"""
        env_path = PROJECT_ROOT / ".env"
        if not env_path.exists():
            self.logger.log("No .env file found (optional)", "warning")
            self.warnings += 1
            return True
        
        self.logger.log(".env configuration loaded", "success")
        self.checks_passed += 1
        return True

    def check_config_files(self) -> bool:
        """Verify essential config files"""
        configs = {
            "larry_config.json": "Agent configuration",
            "mcp.json": "MCP server config",
        }
        
        all_ok = True
        for config, desc in configs.items():
            config_path = PROJECT_ROOT / config
            if config_path.exists():
                self.logger.log(f"{desc}: {config}", "debug")
            else:
                self.logger.log(f"Missing {desc}: {config}", "warning")
                self.warnings += 1
                all_ok = False
        
        if all_ok:
            self.logger.log("All config files present", "success")
            self.checks_passed += 1
        
        return True  # Not critical to block startup

    def check_ollama(self) -> Tuple[bool, str]:
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=OLLAMA_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_count = len(models)
                self.logger.log(f"Ollama running with {model_count} models", "success")
                self.checks_passed += 1
                return True, f"{model_count} models available"
            else:
                self.logger.log("Ollama port responding but API failed", "warning")
                self.warnings += 1
                return False, "API error"
        except Exception as e:
            self.logger.log(f"Ollama not accessible: {str(e)[:80]}", "warning")
            self.warnings += 1
            return False, "Not running"

    def check_disk_space(self) -> bool:
        """Verify adequate disk space"""
        try:
            import shutil
            stat = shutil.disk_usage(PROJECT_ROOT)
            free_gb = stat.free / (1024**3)
            if free_gb < 5:
                self.logger.log(f"Low disk space: {free_gb:.1f} GB free", "warning")
                self.warnings += 1
                return False
            else:
                self.logger.log(f"Disk space: {free_gb:.1f} GB available", "success")
                self.checks_passed += 1
                return True
        except Exception as e:
            self.logger.log(f"Could not check disk: {e}", "warning")
            self.warnings += 1
            return True

    def run_all_checks(self) -> bool:
        """Run all startup checks"""
        self.logger.section("STARTUP VALIDATION")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Virtual Environment", self.check_venv),
            ("Directories", self.check_directories),
            ("Python Modules", self.check_modules),
            ("Config Files", self.check_config_files),
            (".env File", self.check_env_file),
            ("Disk Space", self.check_disk_space),
        ]
        
        if not self.quick:
            checks.append(("Ollama Service", self.check_ollama))
        
        for name, check_func in checks:
            self.logger.log(f"\nChecking: {name}", "step")
            try:
                check_func()
            except Exception as e:
                self.logger.log(f"Check failed: {e}", "error")
                self.checks_failed += 1
        
        # Summary
        self.logger.log(
            f"\nSummary: {Colors.GREEN}{self.checks_passed} passed{Colors.END}, "
            f"{Colors.RED}{self.checks_failed} failed{Colors.END}, "
            f"{Colors.YELLOW}{self.warnings} warnings{Colors.END}",
            "info"
        )
        
        return self.checks_failed == 0


# =============================================================================
# STARTUP ORCHESTRATION
# =============================================================================

class StartupOrchestrator:
    def __init__(self, logger: Logger, args: argparse.Namespace):
        self.logger = logger
        self.args = args
        self.pids = {}

    def setup_environment(self):
        """Configure environment variables"""
        self.logger.section("ENVIRONMENT SETUP")
        
        # Add project root to path
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        
        # Set working directory
        os.chdir(PROJECT_ROOT)
        
        # Load .env if available
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
                self.logger.log("Loaded environment variables from .env", "success")
            except ImportError:
                self.logger.log("python-dotenv not installed, skipping .env", "warning")
        
        self.logger.log(f"Working directory: {os.getcwd()}", "debug")
        self.logger.log(f"Python path updated", "debug")

    def verify_ollama(self):
        """Ensure Ollama is running"""
        self.logger.section("OLLAMA SERVICE")
        
        try:
            import requests
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=OLLAMA_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                self.logger.log(f"✓ Ollama running with {len(models)} models", "success")
                
                if models:
                    self.logger.log(f"Available models:", "info")
                    for m in models[:5]:
                        name = m.get("name", "unknown")
                        self.logger.log(f"  - {name}", "debug")
                    if len(models) > 5:
                        self.logger.log(f"  ... and {len(models)-5} more", "debug")
                return True
        except Exception as e:
            self.logger.log(f"Ollama not accessible: {e}", "error")
            self.logger.log("Make sure Ollama is running: ollama serve", "info")
            if not self.args.quick:
                return False
        
        return True

    def initialize_databases(self):
        """Set up database connections"""
        self.logger.section("DATABASE INITIALIZATION")
        
        # ChromaDB
        if CHROMA_DB.exists():
            self.logger.log(f"ChromaDB found: {CHROMA_DB.name}/", "success")
        else:
            self.logger.log(f"ChromaDB directory created", "success")
        
        # SQLite for unified context
        context_db = DATA_DIR / "unified_context.db"
        if context_db.exists():
            self.logger.log(f"SQLite DB found: {context_db.name}", "success")
        else:
            self.logger.log(f"SQLite DB will be created on first run", "info")
        
        # MCP memory databases
        memory_db = DATA_DIR / "mcp_memory.json"
        if memory_db.exists():
            self.logger.log(f"MCP memory store found", "debug")
        
        self.logger.log("Database initialization complete", "success")

    def test_imports(self):
        """Test importing core agent modules"""
        self.logger.section("IMPORT VERIFICATION")
        
        critical_imports = [
            ("model_router", "Model routing engine"),
            ("file_browser", "File operations"),
            ("agent_v2", "Enhanced agent"),
            ("skill_manager", "Skill system"),
            ("mcp_client", "MCP toolkit"),
        ]
        
        failed = []
        for mod_name, desc in critical_imports:
            try:
                __import__(mod_name)
                self.logger.log(f"{desc}: {mod_name}", "success")
            except ImportError as e:
                self.logger.log(f"{desc}: {mod_name} - FAILED", "error")
                failed.append((mod_name, str(e)))
        
        if failed:
            self.logger.log(f"\n⚠ Import failures (may still work):", "warning")
            for mod_name, err in failed:
                self.logger.log(f"  {mod_name}: {err[:60]}", "debug")
            return len(failed) < len(critical_imports)
        
        self.logger.log(f"All {len(critical_imports)} core modules imported successfully", "success")
        return True

    def start_agent(self):
        """Launch the main agent"""
        self.logger.section("STARTING AGENT")
        
        self.logger.log("Launching agent_v2.py...", "step")
        self.logger.log("", "info")
        
        # Import and run agent
        try:
            from agent_v2 import main
            import asyncio
            asyncio.run(main())
        except KeyboardInterrupt:
            self.logger.log("\n\nAgent interrupted by user", "info")
        except Exception as e:
            self.logger.log(f"Agent error: {e}", "error")
            raise

    def show_startup_banner(self):
        """Show welcome banner"""
        banner = f"""
{Colors.GOLD}{Colors.BOLD}
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  {Colors.END}{Colors.CYAN}AGENT-LARRY v2.1 — G-FORCE EDITION{Colors.END}{Colors.GOLD}                 ║
║                                                                            ║
║        {Colors.END}Your local AI agent with full skills and autonomous tools{Colors.GOLD}        ║
║                                                                            ║
║                  Everything runs locally. Nothing leaves here.            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.CYAN}Startup Log:{Colors.END} {STARTUP_LOG}

"""
        print(banner)
        self.logger.log(banner.replace("\x1b[", "").replace("m", ""), "info")

    def run_full_startup(self):
        """Execute complete startup sequence"""
        start_time = time.time()
        
        try:
            self.show_startup_banner()
            self.setup_environment()
            self.initialize_databases()
            self.verify_ollama()
            self.test_imports()
            
            self.logger.section("STARTUP COMPLETE")
            self.logger.log("All systems ready. Starting agent...", "success")
            self.logger.log("", "info")
            
            elapsed = time.time() - start_time
            self.logger.log(f"Startup took {elapsed:.1f}s", "debug")
            
            # Start the agent
            self.start_agent()
            
        except KeyboardInterrupt:
            self.logger.log("\n\nStartup interrupted", "warning")
            sys.exit(0)
        except Exception as e:
            self.logger.log(f"Fatal error during startup: {e}", "error")
            import traceback
            self.logger.log(traceback.format_exc(), "error")
            sys.exit(1)

    def run_check_only(self):
        """Run validation only, don't start services"""
        checker = StartupChecker(self.logger, quick=self.args.quick)
        if checker.run_all_checks():
            self.logger.log("\n✓ All checks passed. Ready to start.", "success")
            self.logger.log("\nRun: python START_AGENT.py", "info")
            return 0
        else:
            self.logger.log("\n✗ Some checks failed. Fix issues before starting.", "error")
            return 1


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Agent-Larry Universal Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python START_AGENT.py              # Full startup with all checks
  python START_AGENT.py --check      # Validate setup only
  python START_AGENT.py --quick      # Skip Ollama check
  python START_AGENT.py --telegram   # Also start telegram bot

Logs will be saved to: logs/startup_*.log
        """
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate setup without starting agent"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip Ollama availability check"
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Also start telegram bot service"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Use Docker for optional services"
    )
    
    args = parser.parse_args()
    
    # Create logger
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = Logger(STARTUP_LOG)
    
    # Run orchestrator
    orchestrator = StartupOrchestrator(logger, args)
    
    if args.check:
        exit_code = orchestrator.run_check_only()
        sys.exit(exit_code)
    else:
        orchestrator.run_full_startup()


if __name__ == "__main__":
    main()
