#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   INTEGRATION PATCHES — Security Command Center → Larry G-Force     ║
║   Apply these changes to your existing files                        ║
╚══════════════════════════════════════════════════════════════════════╝

Files to modify:
  1. agent_v2.py        → adds /security commands
  2. dashboard_hub.py   → adds security API routes + dashboard tab
  3. security_sentinel.py → hooks into command center for deep scans
  4. larry_config.json   → adds security config section
"""


# ═══════════════════════════════════════════════════════════════════
# 1. AGENT_V2.PY — Add /security command support
# ═══════════════════════════════════════════════════════════════════
#
# Add this import near the top (around line 28):

AGENT_V2_IMPORT = """
# Security Command Center
try:
    from security_command_center import SecurityCommandCenter
    _security_center = SecurityCommandCenter()
    SECURITY_AVAILABLE = True
except ImportError:
    _security_center = None
    SECURITY_AVAILABLE = False
"""

# Add this block inside your command handler (wherever you process /commands).
# In agent_v2.py this is likely in the main input loop or a handle_command() method.
# Look for the pattern: elif cmd == "/tools" or elif cmd == "/kali"
# and add this right next to those:

AGENT_V2_COMMAND_HANDLER = """
elif cmd == "/security" or cmd == "/sec":
    if not SECURITY_AVAILABLE:
        print("\\n⚠️ Security Command Center not available.")
        print("   Place security_command_center.py + port_investigator.py in Agent-Larry dir")
    else:
        # Everything after /security becomes the sub-command
        sec_args = user_input.split(maxsplit=1)[1] if " " in user_input else ""
        output = _security_center.handle_command("security", sec_args)
        print(output)

elif cmd == "/investigate" or cmd == "/ports":
    if not SECURITY_AVAILABLE:
        print("\\n⚠️ Security tools not available")
    else:
        args_text = user_input.split(maxsplit=1)[1] if " " in user_input else ""
        output = _security_center.handle_command("security", f"investigate {args_text}")
        print(output)

elif cmd == "/hunt":
    if not SECURITY_AVAILABLE:
        print("\\n⚠️ Security tools not available")
    else:
        args_text = user_input.split(maxsplit=1)[1] if " " in user_input else ""
        output = _security_center.handle_command("security", f"hunt {args_text}")
        print(output)
"""

# Also add these to your HELP text / command reference:

AGENT_V2_HELP_TEXT = """
  Security

  ┌──────────────────────────────┬─────────────────────────────────────────────┐
  │          Command             │                Description                  │
  ├──────────────────────────────┼─────────────────────────────────────────────┤
  │ /security                    │ Quick security overview                    │
  │ /security investigate        │ Deep port investigation + geolocation      │
  │ /security investigate <port> │ Deep-dive a specific port                  │
  │ /security hunt               │ Network discovery + service scan + OS      │
  │ /security hunt <cidr>        │ Hunt a specific network range              │
  │ /security traffic            │ Traffic analysis + anomaly detection       │
  │ /security firewall           │ Firewall effectiveness test                │
  │ /security audit              │ Full audit (runs ALL modules)              │
  │ /security modules            │ Show available security modules            │
  │ /security export             │ Export last results as JSON                │
  │ /investigate                 │ Alias for /security investigate            │
  │ /investigate <port>          │ Alias for /security investigate <port>     │
  │ /hunt                        │ Alias for /security hunt                   │
  └──────────────────────────────┴─────────────────────────────────────────────┘
"""


# ═══════════════════════════════════════════════════════════════════
# 2. DASHBOARD_HUB.PY — Add security routes + tab
# ═══════════════════════════════════════════════════════════════════
#
# Add these imports near the top (around line 30):

DASHBOARD_IMPORT = """
# Security Command Center
try:
    from security_command_center import SecurityCommandCenter, register_security_routes
    _sec_center = SecurityCommandCenter()
    SECURITY_DASHBOARD = True
except ImportError:
    _sec_center = None
    SECURITY_DASHBOARD = False
"""

# Then after your Flask app is created (after `CORS(app)` around line 38),
# add this:

DASHBOARD_REGISTER = """
# Register security API routes
if SECURITY_DASHBOARD:
    register_security_routes(app, _sec_center)
    logger.info("Security Command Center routes registered")
"""

# This auto-registers these endpoints:
#   GET /api/security/quick       → Fast system overview
#   GET /api/security/investigate  → Port investigation (with ?port=N and ?no_geo=true params)
#   GET /api/security/hunt         → Network discovery (with ?network=CIDR param)
#   GET /api/security/traffic      → Traffic analysis
#   GET /api/security/firewall     → Firewall test (with ?host=IP params)
#   GET /api/security/audit        → Full audit
#   GET /api/security/modules      → Module availability check
#
# To add the security panel to your dashboard HTML, add a tab/link to:
#   /investigate (if you added the port_investigator_panel.html route)
#   or embed the panel inline with a fetch() call to /api/security/quick


# ═══════════════════════════════════════════════════════════════════
# 3. SECURITY_SENTINEL.PY — Hook into Command Center for deep scans
# ═══════════════════════════════════════════════════════════════════
#
# Add this import near the top (around line 34):

SENTINEL_IMPORT = """
# Security Command Center for deep scans
try:
    from security_command_center import SecurityCommandCenter
    _sec_center = SecurityCommandCenter()
    DEEP_SCAN_AVAILABLE = True
except ImportError:
    _sec_center = None
    DEEP_SCAN_AVAILABLE = False
"""

# Replace the existing check_connections() function (lines 287-305)
# with this enhanced version that uses the command center:

SENTINEL_CHECK_CONNECTIONS = """
def check_connections(state: dict) -> list:
    '''Detect connection anomalies + periodic deep investigation.'''
    alerts = []
    try:
        conns = psutil.net_connections(kind="inet")
        established = [c for c in conns if c.status == "ESTABLISHED"]
        current = len(established)
        previous = state.get("known_connections", current)

        if previous > 10 and current > previous * 1.5:
            alerts.append(f"Connection spike: {previous} -> {current} established connections")
        elif current - previous > 30:
            alerts.append(f"Connection surge: +{current - previous} new connections ({current} total)")

        state["known_connections"] = current

        # ── Deep investigation every 6 cycles (~30 min) or on anomaly ──
        scan_count = state.get("investigate_counter", 0) + 1
        state["investigate_counter"] = scan_count

        if DEEP_SCAN_AVAILABLE and (alerts or scan_count % 6 == 0):
            try:
                data = _sec_center.investigate_ports(no_dns=(scan_count % 6 != 0))
                summary = data.get("summary", {})
                state["last_investigation"] = summary
                state["last_investigation_ts"] = data.get("timestamp", "")

                # Track countries — alert on new ones
                known_countries = set(state.get("known_countries", []))
                current_countries = set(data.get("by_country", {}).keys())
                new_countries = current_countries - known_countries - {"Local", "Unknown"}
                if new_countries and known_countries:
                    alerts.append(f"New countries in connections: {', '.join(new_countries)}")
                state["known_countries"] = sorted(current_countries)

                # Send detailed Telegram report on anomaly
                if alerts:
                    pi = None
                    try:
                        from port_investigator import format_telegram_report
                        report = format_telegram_report(data)
                        send_telegram(report, "HTML")
                    except ImportError:
                        pass

            except Exception as e:
                log.warning(f"Deep investigation failed: {e}")

    except Exception as e:
        log.warning(f"Connection check failed: {e}")
    return alerts
"""


# ═══════════════════════════════════════════════════════════════════
# 4. LARRY_CONFIG.JSON — Add security section
# ═══════════════════════════════════════════════════════════════════
#
# Add this section to larry_config.json:

LARRY_CONFIG_SECURITY = """
{
    "security": {
        "command_center_enabled": true,
        "auto_investigate_interval_min": 30,
        "geo_lookup_enabled": true,
        "trusted_countries": ["United States", "Local"],
        "alert_on_new_country": true,
        "deep_scan_on_anomaly": true,
        "reports_dir": "./security_reports",
        "modules": {
            "port_investigator": true,
            "network_hunter": true,
            "traffic_analyzer": true,
            "vps_security_tester": true,
            "autonomous_toolkit": true
        }
    }
}
"""


# ═══════════════════════════════════════════════════════════════════
# 5. NATURAL LANGUAGE ROUTING (for agent_v2.py chat handler)
# ═══════════════════════════════════════════════════════════════════
#
# If you want Larry to respond to natural language security queries
# (e.g., "scan my ports", "check who's connected"), add these
# keyword patterns to your model_router.py or agent_v2.py input handler:

NATURAL_LANGUAGE_PATTERNS = """
# Security-related natural language triggers
# Add to your input processing (before sending to LLM):

SECURITY_TRIGGERS = {
    # Pattern → (command, description)
    r'\\b(scan|check|investigate|show)\\s+(my\\s+)?(ports?|connections?|network)': 
        ('security investigate', 'Port investigation'),
    r'\\b(who|what).*(connected|talking|communicating)': 
        ('security investigate', 'Connection check'),
    r'\\b(hunt|discover|find).*(devices?|hosts?|network)': 
        ('security hunt', 'Network discovery'),
    r'\\b(traffic|flows?|anomal)': 
        ('security traffic', 'Traffic analysis'),
    r'\\b(firewall|blocked|open ports)': 
        ('security firewall', 'Firewall test'),
    r'\\b(full|complete|comprehensive)\\s+(scan|audit|security)': 
        ('security audit', 'Full audit'),
    r'\\b(security|threat)\\s+(status|overview|report)': 
        ('security quick', 'Quick overview'),
}

import re

def check_security_trigger(user_input: str) -> tuple:
    '''Check if input matches a security command trigger.
    Returns (command, description) or (None, None).'''
    text = user_input.lower().strip()
    for pattern, (cmd, desc) in SECURITY_TRIGGERS.items():
        if re.search(pattern, text):
            return cmd, desc
    return None, None

# Usage in your main loop:
#   sec_cmd, sec_desc = check_security_trigger(user_input)
#   if sec_cmd and SECURITY_AVAILABLE:
#       print(f"\\n🛡️ Detected: {sec_desc}")
#       output = _security_center.handle_command(*sec_cmd.split(maxsplit=1))
#       print(output)
#       continue  # skip sending to LLM
"""


# ═══════════════════════════════════════════════════════════════════
# FILE PLACEMENT
# ═══════════════════════════════════════════════════════════════════
#
# Place these files in your Agent-Larry directory:
#
#   ~/Documents/Agent-Larry/
#   ├── security_command_center.py    ← NEW (the unified command center)
#   ├── port_investigator.py          ← NEW (deep port investigation)
#   ├── port_investigator_panel.html  ← NEW (dashboard panel)
#   ├── network_hunter_tools.py       ← EXISTING (you already have this)
#   ├── traffic_analyzer.py           ← EXISTING
#   ├── vps_security_tester.py        ← EXISTING
#   ├── autonomous_security_toolkit.py← EXISTING
#   ├── web_knowledge_extractor.py    ← EXISTING
#   ├── security_sentinel.py          ← MODIFY (apply patches above)
#   ├── agent_v2.py                   ← MODIFY (apply patches above)
#   ├── dashboard_hub.py              ← MODIFY (apply patches above)
#   └── larry_config.json             ← MODIFY (add security section)
#
# That's it. No new dependencies. Everything uses psutil + requests
# (already installed) and the free ip-api.com endpoint (no key needed).
