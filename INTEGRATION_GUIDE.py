# ════════════════════════════════════════════════════════════════
# PORT INVESTIGATOR — Integration Guide for Larry G-Force
# ════════════════════════════════════════════════════════════════
# Drop port_investigator.py into your Agent-Larry directory,
# then apply these patches to your existing files.
#
# Dependencies: NONE new — uses psutil + requests (already installed)
# External API: ip-api.com (free, no key, 45 req/min)
# Resource cost: ~0% VRAM, <1% CPU spike during scan, ~5MB RAM
# ════════════════════════════════════════════════════════════════


# ┌──────────────────────────────────────────────────────────────┐
# │ 1. SECURITY SENTINEL INTEGRATION (security_sentinel.py)      │
# │    Adds /investigate command + periodic deep scan             │
# └──────────────────────────────────────────────────────────────┘

# Add this import near the top of security_sentinel.py (around line 34):
#
#   from port_investigator import (
#       investigate_connections,
#       investigate_port,
#       format_telegram_report,
#       format_investigation_report,
#   )

# Replace the existing check_connections() function (lines 287-305)
# with this enhanced version:

"""
def check_connections(state: dict) -> list:
    '''Detect connection anomalies AND run periodic deep investigation.'''
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

        # ── Deep investigation on anomaly or every 6 cycles (~30 min) ──
        deep_scan_interval = 6
        scan_count = state.get("investigate_counter", 0) + 1
        state["investigate_counter"] = scan_count

        if alerts or scan_count % deep_scan_interval == 0:
            try:
                data = investigate_connections(
                    include_geo=True,
                    include_dns=True,
                    max_dns_lookups=15,
                )
                state["last_investigation"] = data.get("summary", {})
                state["last_investigation_ts"] = data.get("timestamp", "")

                # Check for new/unexpected countries
                known_countries = set(state.get("known_countries", []))
                current_countries = set(data.get("by_country", {}).keys())
                new_countries = current_countries - known_countries - {"Local", "Unknown"}
                if new_countries and known_countries:
                    alerts.append(f"New countries in connections: {', '.join(new_countries)}")
                state["known_countries"] = sorted(current_countries)

                # Telegram deep report on spike
                if alerts:
                    report = format_telegram_report(data)
                    send_telegram(report, "HTML")

            except Exception as e:
                log.warning(f"Deep investigation failed: {e}")

    except Exception as e:
        log.warning(f"Connection check failed: {e}")
    return alerts
"""


# ┌──────────────────────────────────────────────────────────────┐
# │ 2. DASHBOARD HUB INTEGRATION (dashboard_hub.py)              │
# │    Adds /api/investigate endpoint                            │
# └──────────────────────────────────────────────────────────────┘

# Add this import near the top:
#
#   from port_investigator import investigate_connections, investigate_port

# Add these routes (near your other /api/ routes):

"""
@app.route("/api/investigate")
def api_investigate():
    '''Full connection investigation with geolocation.'''
    try:
        data = investigate_connections(
            include_geo=True,
            include_dns=True,
            max_dns_lookups=20,
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/investigate/port/<int:port>")
def api_investigate_port(port):
    '''Deep-dive a specific port.'''
    try:
        data = investigate_port(port)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""


# ┌──────────────────────────────────────────────────────────────┐
# │ 3. AGENT CLI INTEGRATION (agent_v2.py)                       │
# │    Adds /investigate and /ports commands                     │
# └──────────────────────────────────────────────────────────────┘

# Add import:
#   from port_investigator import investigate_connections, investigate_port, format_investigation_report

# Add to your command handler (wherever you process /commands):

"""
elif cmd == "/investigate" or cmd == "/ports":
    args_text = user_input.split(maxsplit=1)[1] if " " in user_input else ""
    if args_text.isdigit():
        # Investigate specific port
        data = investigate_port(int(args_text))
        print(f"\\n🔍 Port {args_text}: {data.get('known_service', 'unknown')}")
        print(f"   {len(data['listeners'])} listeners, {len(data['connections'])} connections")
        for l in data["listeners"]:
            print(f"   🎧 {l.get('process_name','?')} PID:{l.get('pid','?')} up:{l.get('process_uptime_human','?')}")
        for c in data["connections"]:
            geo = c.get("geo", {})
            print(f"   🔗 {c['remote_ip']}:{c['remote_port']} — {geo.get('city','?')}, {geo.get('country','?')}")
    else:
        # Full investigation
        data = investigate_connections(include_geo=True, include_dns=True)
        print(format_investigation_report(data, verbose=True))

elif cmd == "/investigate-json":
    import json as _json
    data = investigate_connections(include_geo=True, include_dns=True)
    print(_json.dumps(data, indent=2, default=str))
"""


# ┌──────────────────────────────────────────────────────────────┐
# │ 4. COMMAND REFERENCE UPDATE                                   │
# │    Add to Agent_Larry_Command_Reference.txt                  │
# └──────────────────────────────────────────────────────────────┘

"""
  Port Investigation

  ┌────────────────────────────┬──────────────────────────────────────────────┐
  │          Command           │                 Description                  │
  ├────────────────────────────┼──────────────────────────────────────────────┤
  │ /investigate               │ Full connection scan with geo, DNS, IO data │
  ├────────────────────────────┼──────────────────────────────────────────────┤
  │ /investigate <port>        │ Deep-dive a specific port                   │
  ├────────────────────────────┼──────────────────────────────────────────────┤
  │ /ports                     │ Alias for /investigate                      │
  ├────────────────────────────┼──────────────────────────────────────────────┤
  │ /investigate-json          │ Raw JSON output (for piping)                │
  └────────────────────────────┴──────────────────────────────────────────────┘
"""
