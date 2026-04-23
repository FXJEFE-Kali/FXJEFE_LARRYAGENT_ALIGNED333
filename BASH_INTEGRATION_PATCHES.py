#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   BASH SCRIPTS → SECURITY COMMAND CENTER INTEGRATION                ║
║   Apply these patches to security_command_center.py and agent_v2.py ║
╚══════════════════════════════════════════════════════════════════════╝

Files to place in Agent-Larry directory:
  bash_script_runner.py          ← NEW
  looting_larry_ultimate.sh      ← EXISTING (you already have)
  larrylekerloco.sh              ← EXISTING
  homelab_security_scan.sh       ← EXISTING
  monitor_homelab.sh             ← EXISTING
  scan_device.sh                 ← EXISTING
  scan_ipv6_local.sh             ← EXISTING
  verify_network.sh              ← EXISTING
"""


# ═══════════════════════════════════════════════════════════════════
# 1. SECURITY_COMMAND_CENTER.PY — Add bash runner integration
# ═══════════════════════════════════════════════════════════════════

# Add to the _LazyModules class (around line 110):

LAZY_BASH_RUNNER = """
    @classmethod
    def bash_runner(cls):
        if "br" not in cls._cache:
            try:
                from bash_script_runner import BashScriptRunner
                cls._cache["br"] = BashScriptRunner()
            except ImportError as e:
                log.warning(f"bash_script_runner not available: {e}")
                cls._cache["br"] = None
        return cls._cache["br"]
"""

# Add these methods to the SecurityCommandCenter class:

SEC_CMD_BASH_METHODS = '''
    # ══════════════════════════════════════════════════════════════
    #  OPERATION: BASH SCRIPTS
    # ══════════════════════════════════════════════════════════════

    def run_bash_script(self, key: str, extra_args: list = None) -> Dict:
        """Run a bash security script by key."""
        runner = Lazy.bash_runner()
        if not runner:
            return {"error": "bash_script_runner.py not found"}
        return runner.run(key, extra_args=extra_args)

    def list_bash_scripts(self) -> Dict:
        """List all available bash scripts."""
        runner = Lazy.bash_runner()
        if not runner:
            return {"error": "bash_script_runner.py not found"}
        return runner.list_scripts()
'''

# Add to the handle_command() method, alongside the existing elif blocks:

SEC_CMD_BASH_HANDLER = '''
        elif subcmd in ("bash", "scripts", "sh"):
            runner = Lazy.bash_runner()
            if not runner:
                return "\\n⚠️  bash_script_runner.py not found"
            bash_args = " ".join(subargs) if subargs else ""
            return runner.handle_command(bash_args)

        elif subcmd in ("verify", "network-check"):
            runner = Lazy.bash_runner()
            if not runner:
                return "\\n⚠️  bash_script_runner.py not found"
            return runner.handle_command("verify")

        elif subcmd in ("scan-device", "deep-scan"):
            runner = Lazy.bash_runner()
            if not runner:
                return "\\n⚠️  bash_script_runner.py not found"
            target = subargs[0] if subargs else ""
            if not target:
                return "\\nUsage: /security scan-device <ip>"
            return runner.handle_command(f"scan {target}")

        elif subcmd in ("homelab", "nmap-audit"):
            runner = Lazy.bash_runner()
            if not runner:
                return "\\n⚠️  bash_script_runner.py not found"
            return runner.handle_command("audit")

        elif subcmd in ("looting", "ll"):
            runner = Lazy.bash_runner()
            if not runner:
                return "\\n⚠️  bash_script_runner.py not found"
            return runner.handle_command("looting")
'''

# Update the help text in handle_command() to include bash commands:

SEC_CMD_UPDATED_HELP = '''
            return (
                "\\n🛡️  Security Commands:\\n"
                "\\n   Python Modules:\\n"
                "   /security              Quick overview\\n"
                "   /security investigate   Port investigation + geo\\n"
                "   /security investigate N Deep-dive port N\\n"
                "   /security hunt          Network discovery\\n"
                "   /security traffic       Traffic analysis\\n"
                "   /security firewall      Firewall test\\n"
                "   /security audit         Full audit (all modules)\\n"
                "   /security modules       Show available modules\\n"
                "   /security export        Export results as JSON\\n"
                "\\n   Bash Scripts:\\n"
                "   /security bash          List all bash scripts\\n"
                "   /security verify        Network config check\\n"
                "   /security scan-device IP Deep nmap scan of a device\\n"
                "   /security homelab       Full homelab nmap audit\\n"
                "   /security looting       Looting Larry menu\\n"
                "   /security bash run KEY  Run any script by key\\n"
                "\\n   /bash                  Direct bash script access"
            )
'''


# ═══════════════════════════════════════════════════════════════════
# 2. AGENT_V2.PY — Add /bash command
# ═══════════════════════════════════════════════════════════════════

AGENT_V2_BASH_IMPORT = """
# Bash Script Runner
try:
    from bash_script_runner import BashScriptRunner
    _bash_runner = BashScriptRunner()
    BASH_SCRIPTS_AVAILABLE = True
except ImportError:
    _bash_runner = None
    BASH_SCRIPTS_AVAILABLE = False
"""

AGENT_V2_BASH_HANDLER = """
elif cmd == "/bash" or cmd == "/sh":
    if not BASH_SCRIPTS_AVAILABLE:
        print("\\n⚠️  bash_script_runner.py not found")
    else:
        bash_args = user_input.split(maxsplit=1)[1] if " " in user_input else ""
        output = _bash_runner.handle_command(bash_args)
        if output:
            print(output)
"""


# ═══════════════════════════════════════════════════════════════════
# 3. DASHBOARD_HUB.PY — Add bash script API routes
# ═══════════════════════════════════════════════════════════════════

DASHBOARD_BASH_ROUTES = """
# Add these routes alongside the security routes:

@app.route("/api/bash/list")
def api_bash_list():
    '''List available bash security scripts.'''
    try:
        from bash_script_runner import BashScriptRunner
        runner = BashScriptRunner()
        return jsonify(runner.list_scripts())
    except ImportError:
        return jsonify({"error": "bash_script_runner not available"}), 500

@app.route("/api/bash/run/<key>")
def api_bash_run(key):
    '''Run a bash script (non-interactive only).'''
    from flask import request
    try:
        from bash_script_runner import BashScriptRunner, SCRIPT_REGISTRY
        runner = BashScriptRunner()
        info = SCRIPT_REGISTRY.get(key)
        if not info:
            return jsonify({"error": f"Unknown script: {key}"}), 404
        if info.interactive:
            return jsonify({"error": f"{info.name} is interactive — run from terminal"}), 400
        extra = request.args.getlist("arg")
        result = runner.run(key, extra_args=extra or None, stream_output=False)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bash/verify")
def api_bash_verify():
    '''Run network verification script.'''
    try:
        from bash_script_runner import BashScriptRunner
        runner = BashScriptRunner()
        result = runner.run("verify-network", stream_output=False)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""


# ═══════════════════════════════════════════════════════════════════
# 4. UPDATED COMMAND REFERENCE
# ═══════════════════════════════════════════════════════════════════

COMMAND_REFERENCE = """
  Bash Security Scripts

  ┌───────────────────────────────┬─────────────────────────────────────────────┐
  │           Command             │                Description                  │
  ├───────────────────────────────┼─────────────────────────────────────────────┤
  │ /bash                         │ List available bash scripts                │
  │ /bash verify                  │ Network config check (no sudo)             │
  │ /bash scan <ip>               │ Deep nmap scan of a specific device        │
  │ /bash audit                   │ Full homelab security audit (4 phases)     │
  │ /bash looting                 │ Launch Looting Larry interactive menu      │
  │ /bash looting-scan            │ Quick Looting Larry discovery scan         │
  │ /bash monitor                 │ Start baseline diff monitor                │
  │ /bash ipv6                    │ IPv6 link-local scan                       │
  │ /bash run <key> [args]        │ Run any registered script by key           │
  ├───────────────────────────────┼─────────────────────────────────────────────┤
  │ /security bash                │ Same as /bash (via security center)        │
  │ /security verify              │ Same as /bash verify                       │
  │ /security scan-device <ip>    │ Same as /bash scan <ip>                    │
  │ /security homelab             │ Same as /bash audit                        │
  │ /security looting             │ Same as /bash looting                      │
  └───────────────────────────────┴─────────────────────────────────────────────┘

  Script Keys (for /bash run <key>):
    looting          Looting Larry interactive menu
    looting-scan     Single automated discovery scan
    looting-daemon   Start hourly scan daemon
    lekerloco        Larry Leker Loco interactive
    lekerloco-scan   Single automated scan
    homelab-audit    Full 4-phase nmap audit
    homelab-monitor  Continuous baseline monitor
    scan-device      Deep scan (requires IP arg)
    scan-ipv6        IPv6 link-local discovery
    verify-network   Network config check
"""


# ═══════════════════════════════════════════════════════════════════
# 5. NATURAL LANGUAGE PATTERNS (add to existing triggers)
# ═══════════════════════════════════════════════════════════════════

BASH_NLP_TRIGGERS = """
# Add these to the SECURITY_TRIGGERS dict in agent_v2.py:

    r'\\b(run|launch|start)\\s+(looting|larry)':
        ('bash looting', 'Looting Larry'),
    r'\\b(deep|full)\\s+(scan|nmap)\\s+[0-9]':
        ('bash scan', 'Device deep scan'),
    r'\\b(homelab|home\\s+lab)\\s+(scan|audit|security)':
        ('bash audit', 'Homelab security audit'),
    r'\\b(verify|check)\\s+(network|config|vpn|dns)':
        ('bash verify', 'Network verification'),
    r'\\b(monitor|watch|baseline)\\s+(network|homelab|devices)':
        ('bash monitor', 'Homelab monitor'),
    r'\\bipv6\\s+(scan|discover)':
        ('bash ipv6', 'IPv6 local scan'),
"""


# ═══════════════════════════════════════════════════════════════════
# FILE LAYOUT
# ═══════════════════════════════════════════════════════════════════
#
# ~/Documents/Agent-Larry/
# ├── security_command_center.py    ← Python orchestrator (all modules)
# ├── bash_script_runner.py         ← NEW — bash script wrapper
# ├── port_investigator.py          ← Deep port investigation
# ├── network_hunter_tools.py       ← Python network hunter
# ├── traffic_analyzer.py           ← Python traffic analyzer
# ├── vps_security_tester.py        ← Python VPS tester
# ├── autonomous_security_toolkit.py← Python autonomous toolkit
# ├── security_sentinel.py          ← Robin (patrol daemon)
# ├── agent_v2.py                   ← Main agent CLI
# ├── dashboard_hub.py              ← Web dashboard
# │
# ├── looting_larry_ultimate.sh     ← Bash: SQLite scanner
# ├── larrylekerloco.sh             ← Bash: persistent scanner
# ├── homelab_security_scan.sh      ← Bash: 4-phase nmap audit
# ├── monitor_homelab.sh            ← Bash: baseline diff monitor
# ├── scan_device.sh                ← Bash: deep single-device scan
# ├── scan_ipv6_local.sh            ← Bash: IPv6 discovery
# └── verify_network.sh             ← Bash: network config check
