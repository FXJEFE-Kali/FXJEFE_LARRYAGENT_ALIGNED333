#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   LARRY G-FORCE — Bash Script Runner                                ║
║   Integrates shell-based security scripts into the command center   ║
╚══════════════════════════════════════════════════════════════════════╝

Wraps these scripts with Python orchestration:
  - looting_larry_ultimate.sh   → SQLite-backed network scanner
  - larrylekerloco.sh           → Persistent scanner with systemd/cron
  - homelab_security_scan.sh    → Full 4-phase nmap audit
  - monitor_homelab.sh          → Baseline diff monitor
  - scan_device.sh              → Deep single-device scan
  - scan_ipv6_local.sh          → IPv6 link-local scanner
  - verify_network.sh           → Network config verification

Each script runs as a subprocess with:
  - Live output streaming to terminal
  - Timeout protection
  - Automatic sudo handling
  - Output capture for reports
  - Integration with port_investigator for enrichment
"""

import os
import sys
import json
import signal
import subprocess
import threading
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict

log = logging.getLogger("bash_runner")

# ── Script Registry ──────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()

@dataclass
class ScriptInfo:
    """Metadata for a bash security script."""
    name: str
    filename: str
    description: str
    category: str           # discovery, audit, monitor, device, utility
    needs_sudo: bool
    needs_nmap: bool
    default_args: List[str]
    timeout_sec: int
    interactive: bool       # requires user input (can't run headless)

# All known scripts — the runner discovers which ones are actually present
SCRIPT_REGISTRY: Dict[str, ScriptInfo] = {
    "looting": ScriptInfo(
        name="Looting Larry",
        filename="looting_larry_ultimate.sh",
        description="Full network scanner with SQLite DB, daemon mode, cron scheduling",
        category="discovery",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],
        timeout_sec=600,
        interactive=True,
    ),
    "looting-scan": ScriptInfo(
        name="Looting Larry (scan once)",
        filename="looting_larry_ultimate.sh",
        description="Run a single automated network discovery scan",
        category="discovery",
        needs_sudo=True,
        needs_nmap=True,
        default_args=["--scan-once"],
        timeout_sec=300,
        interactive=False,
    ),
    "looting-daemon": ScriptInfo(
        name="Looting Larry (daemon)",
        filename="looting_larry_ultimate.sh",
        description="Start background daemon for hourly scans",
        category="monitor",
        needs_sudo=True,
        needs_nmap=True,
        default_args=["--daemon"],
        timeout_sec=0,  # runs indefinitely
        interactive=False,
    ),
    "lekerloco": ScriptInfo(
        name="Larry Leker Loco",
        filename="larrylekerloco.sh",
        description="Persistent scanner with systemd/cron/launchd support",
        category="discovery",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],
        timeout_sec=600,
        interactive=True,
    ),
    "lekerloco-scan": ScriptInfo(
        name="Leker Loco (scan once)",
        filename="larrylekerloco.sh",
        description="Single automated scan with DB logging",
        category="discovery",
        needs_sudo=True,
        needs_nmap=True,
        default_args=["--scan-once"],
        timeout_sec=300,
        interactive=False,
    ),
    "homelab-audit": ScriptInfo(
        name="Homelab Security Audit",
        filename="homelab_security_scan.sh",
        description="Full 4-phase nmap audit: discovery, ports, services, vulns",
        category="audit",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],
        timeout_sec=900,
        interactive=False,
    ),
    "homelab-monitor": ScriptInfo(
        name="Homelab Monitor",
        filename="monitor_homelab.sh",
        description="Continuous baseline diff monitor (alerts on new devices)",
        category="monitor",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],
        timeout_sec=0,  # runs indefinitely
        interactive=True,
    ),
    "scan-device": ScriptInfo(
        name="Device Deep Scan",
        filename="scan_device.sh",
        description="Full TCP scan + service detection + OS + vulns on single device",
        category="device",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],  # requires IP argument
        timeout_sec=600,
        interactive=False,
    ),
    "scan-ipv6": ScriptInfo(
        name="IPv6 Local Scanner",
        filename="scan_ipv6_local.sh",
        description="Discover and scan IPv6 link-local hosts",
        category="discovery",
        needs_sudo=True,
        needs_nmap=True,
        default_args=[],
        timeout_sec=120,
        interactive=False,
    ),
    "verify-network": ScriptInfo(
        name="Network Verification",
        filename="verify_network.sh",
        description="Check local IPs, gateway, public IP, VPN status, DNS",
        category="utility",
        needs_sudo=False,
        needs_nmap=False,
        default_args=[],
        timeout_sec=30,
        interactive=False,
    ),
}

# Alternate filenames to search for
ALTERNATE_FILENAMES = {
    "looting_larry_ultimate1.sh": "looting",
}


class BashScriptRunner:
    """
    Discovers, validates, and executes bash security scripts.
    Integrates with SecurityCommandCenter for unified access.
    """

    def __init__(self, script_dirs: List[str] = None):
        self.script_dirs = [
            str(SCRIPT_DIR),
            str(Path.home() / "Documents" / "Agent-Larry"),
            str(Path.home() / "looting_larry"),
            str(Path.home()),
        ]
        if script_dirs:
            self.script_dirs = script_dirs + self.script_dirs

        self.available_scripts: Dict[str, Path] = {}
        self._discover_scripts()

    def _discover_scripts(self):
        """Find which scripts actually exist on disk."""
        self.available_scripts.clear()
        seen_files = set()

        for key, info in SCRIPT_REGISTRY.items():
            for search_dir in self.script_dirs:
                path = Path(search_dir) / info.filename
                if path.exists() and path.name not in seen_files:
                    self.available_scripts[key] = path
                    seen_files.add(path.name)
                    break

        # Check alternates
        for alt_name, registry_key in ALTERNATE_FILENAMES.items():
            if registry_key not in self.available_scripts:
                for search_dir in self.script_dirs:
                    path = Path(search_dir) / alt_name
                    if path.exists():
                        self.available_scripts[registry_key] = path
                        break

        log.info(f"Discovered {len(self.available_scripts)} bash scripts")

    def list_scripts(self) -> Dict[str, dict]:
        """List all scripts with availability status."""
        result = {}
        for key, info in SCRIPT_REGISTRY.items():
            available = key in self.available_scripts
            result[key] = {
                "name": info.name,
                "description": info.description,
                "category": info.category,
                "available": available,
                "path": str(self.available_scripts.get(key, "")),
                "needs_sudo": info.needs_sudo,
                "needs_nmap": info.needs_nmap,
                "interactive": info.interactive,
            }
        return result

    def list_available(self) -> Dict[str, dict]:
        """List only available scripts."""
        return {k: v for k, v in self.list_scripts().items() if v["available"]}

    def check_prerequisites(self, key: str) -> Tuple[bool, List[str]]:
        """Check if a script can run (sudo, nmap, etc)."""
        if key not in SCRIPT_REGISTRY:
            return False, [f"Unknown script: {key}"]

        info = SCRIPT_REGISTRY[key]
        issues = []

        if key not in self.available_scripts:
            issues.append(f"Script not found: {info.filename}")

        if info.needs_nmap and not _cmd_exists("nmap"):
            issues.append("nmap not installed (apt install nmap)")

        if info.needs_sudo and os.geteuid() != 0 and not _can_sudo():
            issues.append("Requires sudo — run with elevated privileges or configure NOPASSWD")

        return len(issues) == 0, issues

    # ── Execute Script ────────────────────────────────────────────

    def run(self, key: str, extra_args: List[str] = None,
            stream_output: bool = True, timeout: int = None,
            capture: bool = True) -> Dict:
        """
        Run a bash script by registry key.

        Args:
            key: Script key from SCRIPT_REGISTRY
            extra_args: Additional command-line arguments
            stream_output: Print output live to terminal
            timeout: Override default timeout (0 = no timeout)
            capture: Capture stdout/stderr for return value

        Returns:
            {success, exit_code, stdout, stderr, duration_sec, script_info}
        """
        if key not in SCRIPT_REGISTRY:
            return {"success": False, "error": f"Unknown script: {key}"}

        info = SCRIPT_REGISTRY[key]

        if key not in self.available_scripts:
            return {"success": False, "error": f"Script not found: {info.filename}",
                    "hint": f"Place {info.filename} in {SCRIPT_DIR}"}

        script_path = self.available_scripts[key]

        # Prerequisites check
        ok, issues = self.check_prerequisites(key)
        if not ok:
            return {"success": False, "error": "Prerequisites not met",
                    "issues": issues}

        # Build command
        cmd = []
        if info.needs_sudo and os.geteuid() != 0:
            cmd.extend(["sudo", "bash"])
        else:
            cmd.append("bash")

        cmd.append(str(script_path))
        cmd.extend(info.default_args)
        if extra_args:
            cmd.extend(extra_args)

        effective_timeout = timeout if timeout is not None else info.timeout_sec
        if effective_timeout == 0:
            effective_timeout = None  # no timeout for daemons

        log.info(f"Running: {' '.join(cmd)}")

        start = time.time()
        result = {
            "script": key,
            "name": info.name,
            "command": " ".join(cmd),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }

        try:
            if stream_output and not capture:
                # Interactive mode — direct terminal passthrough
                proc = subprocess.run(
                    cmd,
                    timeout=effective_timeout,
                    cwd=str(script_path.parent),
                )
                result["exit_code"] = proc.returncode
                result["success"] = proc.returncode == 0

            elif stream_output and capture:
                # Stream + capture — line-buffered
                stdout_lines = []
                stderr_lines = []

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    cwd=str(script_path.parent),
                )

                # Stream stdout
                def _read_stream(stream, store, prefix=""):
                    for line in stream:
                        store.append(line)
                        if stream_output:
                            sys.stdout.write(f"{prefix}{line}")
                            sys.stdout.flush()

                t_out = threading.Thread(target=_read_stream, args=(proc.stdout, stdout_lines))
                t_err = threading.Thread(target=_read_stream, args=(proc.stderr, stderr_lines, "ERR: "))
                t_out.start()
                t_err.start()

                try:
                    proc.wait(timeout=effective_timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    result["error"] = f"Timeout after {effective_timeout}s"

                t_out.join(timeout=5)
                t_err.join(timeout=5)

                result["exit_code"] = proc.returncode
                result["success"] = proc.returncode == 0
                result["stdout"] = "".join(stdout_lines)
                result["stderr"] = "".join(stderr_lines)

            else:
                # Silent capture
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                    cwd=str(script_path.parent),
                )
                result["exit_code"] = proc.returncode
                result["success"] = proc.returncode == 0
                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr

        except subprocess.TimeoutExpired:
            result["error"] = f"Script timed out after {effective_timeout}s"
        except FileNotFoundError:
            result["error"] = f"Script not found: {script_path}"
        except PermissionError:
            result["error"] = "Permission denied — try running with sudo"
        except Exception as e:
            result["error"] = str(e)

        result["duration_sec"] = round(time.time() - start, 2)
        return result

    def run_verify_network(self) -> Dict:
        """Quick network verification — no sudo needed."""
        return self.run("verify-network", stream_output=True)

    def run_device_scan(self, target_ip: str) -> Dict:
        """Deep scan a specific device."""
        return self.run("scan-device", extra_args=[target_ip])

    def run_homelab_audit(self) -> Dict:
        """Full 4-phase homelab security audit."""
        return self.run("homelab-audit")

    def run_looting_scan(self) -> Dict:
        """Single Looting Larry network discovery scan."""
        return self.run("looting-scan")

    def run_looting_interactive(self):
        """Launch full Looting Larry interactive menu."""
        return self.run("looting", stream_output=True, capture=False)

    # ── Formatted Output ──────────────────────────────────────────

    def format_script_list(self) -> str:
        """Format available scripts for terminal display."""
        lines = [
            "",
            "🐚 BASH SECURITY SCRIPTS",
            "",
        ]

        categories = {}
        for key, info in SCRIPT_REGISTRY.items():
            cat = info.category
            if cat not in categories:
                categories[cat] = []
            available = key in self.available_scripts
            icon = "✓" if available else "✗"
            interactive = " [interactive]" if info.interactive else ""
            categories[cat].append(
                f"   {icon} {key:20s} {info.name}{interactive}"
            )

        cat_icons = {"discovery": "🔍", "audit": "🛡️", "monitor": "📡",
                     "device": "🎯", "utility": "🔧"}

        for cat, items in categories.items():
            lines.append(f"   {cat_icons.get(cat, '📦')} {cat.upper()}")
            lines.extend(items)
            lines.append("")

        return "\n".join(lines)

    # ── Command Router (for agent CLI) ────────────────────────────

    def handle_command(self, args: str = "") -> str:
        """
        Process /bash commands from agent_v2.py.

        Commands:
          /bash                    List available scripts
          /bash list               Same as above
          /bash verify             Run verify_network.sh
          /bash scan <ip>          Deep scan a device
          /bash audit              Homelab security audit
          /bash looting            Launch Looting Larry menu
          /bash looting-scan       Quick Looting Larry scan
          /bash monitor            Start homelab monitor
          /bash ipv6               IPv6 local scan
          /bash run <key> [args]   Run any script by key
        """
        parts = args.strip().split() if args.strip() else []
        subcmd = parts[0] if parts else "list"
        subargs = parts[1:] if len(parts) > 1 else []

        if subcmd in ("list", "scripts", "ls"):
            return self.format_script_list()

        elif subcmd in ("verify", "network", "net"):
            result = self.run_verify_network()
            return result.get("stdout", result.get("error", "Failed"))

        elif subcmd in ("scan", "device") and subargs:
            target = subargs[0]
            print(f"\n🎯 Deep scanning {target}...")
            result = self.run_device_scan(target)
            return f"\n{'✓' if result['success'] else '✗'} Scan {'complete' if result['success'] else 'failed'} ({result.get('duration_sec', '?')}s)"

        elif subcmd in ("audit", "homelab-audit", "full"):
            print("\n🛡️ Starting homelab security audit...")
            result = self.run_homelab_audit()
            return f"\n{'✓' if result['success'] else '✗'} Audit {'complete' if result['success'] else 'failed'} ({result.get('duration_sec', '?')}s)"

        elif subcmd in ("looting", "ll"):
            self.run_looting_interactive()
            return ""

        elif subcmd in ("looting-scan", "ll-scan", "discovery"):
            print("\n🔍 Running Looting Larry discovery scan...")
            result = self.run_looting_scan()
            return f"\n{'✓' if result['success'] else '✗'} Discovery {'complete' if result['success'] else 'failed'} ({result.get('duration_sec', '?')}s)"

        elif subcmd in ("monitor", "watch"):
            print("\n📡 Starting homelab monitor (Ctrl+C to stop)...")
            self.run("homelab-monitor", stream_output=True, capture=False)
            return ""

        elif subcmd in ("ipv6",):
            print("\n🔍 Scanning IPv6 link-local...")
            result = self.run("scan-ipv6")
            return result.get("stdout", result.get("error", "Failed"))

        elif subcmd == "run" and subargs:
            key = subargs[0]
            extra = subargs[1:] if len(subargs) > 1 else None
            info = SCRIPT_REGISTRY.get(key)
            if not info:
                return f"\n✗ Unknown script: {key}. Use /bash list to see available scripts."
            print(f"\n🐚 Running {info.name}...")
            if info.interactive:
                result = self.run(key, extra_args=extra, stream_output=True, capture=False)
            else:
                result = self.run(key, extra_args=extra)
            return f"\n{'✓' if result.get('success') else '✗'} {info.name} {'complete' if result.get('success') else 'failed'}"

        else:
            return (
                "\n🐚 Bash Script Commands:\n"
                "   /bash                List available scripts\n"
                "   /bash verify         Network config check\n"
                "   /bash scan <ip>      Deep scan a device\n"
                "   /bash audit          Full homelab audit (nmap)\n"
                "   /bash looting        Looting Larry menu\n"
                "   /bash looting-scan   Quick network discovery\n"
                "   /bash monitor        Continuous baseline monitor\n"
                "   /bash ipv6           IPv6 local scan\n"
                "   /bash run <key>      Run any script by key"
            )


# ── Utilities ─────────────────────────────────────────────────────

def _cmd_exists(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _can_sudo() -> bool:
    """Check if current user can sudo without password."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


# ── CLI Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bash Script Runner for Larry G-Force")
    parser.add_argument("command", nargs="?", default="list",
                        help="Command: list, verify, scan, audit, looting, monitor, ipv6, run")
    parser.add_argument("args", nargs="*", help="Additional arguments")

    args = parser.parse_args()
    runner = BashScriptRunner()

    cmd_str = f"{args.command} {' '.join(args.args)}".strip()
    output = runner.handle_command(cmd_str)
    if output:
        print(output)
