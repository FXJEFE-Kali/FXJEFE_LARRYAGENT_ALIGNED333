#!/usr/bin/env python3
"""
Resource Governor — Larry G-Force adaptive resource manager.
================================================================
Keeps CPU, GPU, and RAM under configurable ceilings (default 90%).

Strategies:
  CPU  > ceiling  → renice Ollama runners to nice=15 (reduces scheduling share)
  CPU  < restore  → renice back to 0
  GPU  > ceiling  → lower nvidia power limit (floor: 90W)
  GPU  < restore  → restore to default power limit (115W)
  RAM  > ceiling  → evict the oldest loaded Ollama model via keep_alive=0
  RAM  < restore  → nothing (kernel will refill cache naturally)

Runs as a daemon, emits to ActivityStream, optionally reports via Telegram.
Can also be imported and queried from other modules.

Usage:
  python3 resource_governor.py           # run daemon
  python3 resource_governor.py --status  # print one-shot status
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

import psutil

# ── Config ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_FILE   = SCRIPT_DIR / "logs" / "governor.log"
STATE_FILE = SCRIPT_DIR / "logs" / "governor_state.json"
(SCRIPT_DIR / "logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GOV] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Thresholds ───────────────────────────────────────────────────────
CPU_CEILING   = 90   # % — throttle when system CPU exceeds this
CPU_RESTORE   = 72   # % — de-throttle when CPU drops below this
GPU_CEILING   = 90   # % utilization
GPU_RESTORE   = 72   # %
RAM_CEILING   = 85   # % — evict oldest Ollama model when RAM exceeds this
RAM_RESTORE   = 70   # %

GPU_POWER_DEFAULT = 115  # W — restore target (your card's default)
GPU_POWER_FLOOR   = 90   # W — minimum power limit (card's reported min)
GPU_POWER_STEP    = 10   # W — step down per throttle action

POLL_INTERVAL = 15   # seconds between checks
OLLAMA_URL    = "http://localhost:11434"

# Processes we're allowed to renice (by name match)
RENICEABLE = {"ollama runner", "ollama", "python3", "python"}

# ── ActivityStream (optional) ────────────────────────────────────────
try:
    from activity_stream import ActivityStream
    _activity = ActivityStream("governor")
except ImportError:
    _activity = None

def _emit(msg: str, data: dict = None):
    if _activity:
        _activity.emit("governor", msg, data or {})
    log.info(msg)


# ── GPU helpers (via nvidia-smi) ─────────────────────────────────────

def gpu_stats() -> Optional[dict]:
    """Return dict with gpu_util, mem_util, power_draw, power_limit or None."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,utilization.memory,power.draw,power.limit,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            text=True, timeout=5
        ).strip().split(",")
        if len(out) < 6:
            return None
        return {
            "gpu_util":    float(out[0].strip()),
            "mem_util":    float(out[1].strip()),
            "power_draw":  float(out[2].strip()),
            "power_limit": float(out[3].strip()),
            "vram_used_mb": float(out[4].strip()),
            "vram_total_mb": float(out[5].strip()),
        }
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return None


def set_gpu_power_limit(watts: float) -> bool:
    """Set GPU power limit via nvidia-smi. Returns True on success."""
    watts = max(GPU_POWER_FLOOR, min(GPU_POWER_DEFAULT, round(watts)))
    try:
        result = subprocess.run(
            ["sudo", "nvidia-smi", "-pl", str(watts)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            _emit(f"GPU power limit set to {watts}W")
            return True
        else:
            log.warning(f"nvidia-smi -pl failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        log.warning(f"set_gpu_power_limit failed: {e}")
        return False


# ── CPU helpers (renice) ─────────────────────────────────────────────

def _ollama_runner_pids() -> list:
    """Find all ollama runner process PIDs."""
    pids = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if "ollama" in name or "ollama runner" in cmdline:
                pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


def renice_pids(pids: list, nice_val: int):
    """Set scheduling priority for a list of PIDs via renice."""
    for pid in pids:
        try:
            subprocess.run(
                ["renice", "-n", str(nice_val), "-p", str(pid)],
                capture_output=True, text=True, timeout=5
            )
        except Exception:
            pass


# ── RAM / Ollama model eviction ───────────────────────────────────────

def ollama_loaded_models() -> list:
    """Return list of currently loaded models from Ollama API, oldest first."""
    try:
        import urllib.request
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/ps", timeout=5) as resp:
            data = json.loads(resp.read())
        models = data.get("models", [])
        # Sort by expires_at ascending (evict earliest-expiring = least recently used)
        models.sort(key=lambda m: m.get("expires_at", ""))
        return models
    except Exception:
        return []


def evict_oldest_model() -> Optional[str]:
    """Ask Ollama to unload the oldest loaded model. Returns model name or None."""
    models = ollama_loaded_models()
    if not models:
        return None
    target = models[0]["name"]
    try:
        import urllib.request, urllib.error
        payload = json.dumps({"model": target, "keep_alive": 0}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        _emit(f"Evicted Ollama model to free RAM: {target}")
        return target
    except Exception as e:
        log.warning(f"Model eviction failed for {target}: {e}")
        return None


# ── State ─────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "cpu_throttled": False,
        "gpu_throttled": False,
        "current_power_limit": GPU_POWER_DEFAULT,
        "evictions": 0,
        "throttle_count": 0,
        "last_check": 0,
    }


def save_state(state: dict):
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


# ── Snapshot (queryable from other modules) ───────────────────────────

def get_snapshot() -> dict:
    """Return current resource snapshot. Safe to call from any thread."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    gpu = gpu_stats()
    state = load_state()
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_pct": cpu,
        "cpu_throttled": state.get("cpu_throttled", False),
        "ram_pct": mem.percent,
        "ram_used_gb": round(mem.used / 1e9, 1),
        "ram_total_gb": round(mem.total / 1e9, 1),
        "gpu": gpu,
        "gpu_throttled": state.get("gpu_throttled", False),
        "current_power_limit_w": state.get("current_power_limit", GPU_POWER_DEFAULT),
        "thresholds": {
            "cpu_ceiling": CPU_CEILING,
            "gpu_ceiling": GPU_CEILING,
            "ram_ceiling": RAM_CEILING,
        },
        "evictions": state.get("evictions", 0),
        "throttle_count": state.get("throttle_count", 0),
    }


# ── Governor cycle ────────────────────────────────────────────────────

def run_governor_cycle(state: dict) -> list:
    """
    Check all resources. Apply throttling as needed.
    Returns list of action strings taken this cycle.
    """
    actions = []

    # ── CPU ──────────────────────────────────────────────────────
    cpu = psutil.cpu_percent(interval=1)

    if cpu > CPU_CEILING and not state["cpu_throttled"]:
        pids = _ollama_runner_pids()
        if pids:
            renice_pids(pids, nice_val=15)
            state["cpu_throttled"] = True
            state["throttle_count"] = state.get("throttle_count", 0) + 1
            msg = f"CPU {cpu:.0f}% > {CPU_CEILING}% — reniced {len(pids)} Ollama runner(s) to nice=15"
            actions.append(msg)
            _emit(msg, {"cpu": cpu, "pids": pids})

    elif cpu < CPU_RESTORE and state["cpu_throttled"]:
        pids = _ollama_runner_pids()
        if pids:
            renice_pids(pids, nice_val=0)
        state["cpu_throttled"] = False
        msg = f"CPU {cpu:.0f}% < {CPU_RESTORE}% — restored Ollama nice=0"
        actions.append(msg)
        _emit(msg, {"cpu": cpu})

    # ── GPU ──────────────────────────────────────────────────────
    gstats = gpu_stats()
    if gstats:
        gpu_util = gstats["gpu_util"]
        cur_limit = state.get("current_power_limit", GPU_POWER_DEFAULT)

        if gpu_util > GPU_CEILING and cur_limit > GPU_POWER_FLOOR:
            new_limit = max(GPU_POWER_FLOOR, cur_limit - GPU_POWER_STEP)
            if set_gpu_power_limit(new_limit):
                state["gpu_throttled"] = True
                state["current_power_limit"] = new_limit
                state["throttle_count"] = state.get("throttle_count", 0) + 1
                msg = (f"GPU {gpu_util:.0f}% > {GPU_CEILING}% — "
                       f"power limit {cur_limit:.0f}W → {new_limit:.0f}W")
                actions.append(msg)
                _emit(msg, {"gpu_util": gpu_util, "power_limit": new_limit})

        elif gpu_util < GPU_RESTORE and state["gpu_throttled"] and cur_limit < GPU_POWER_DEFAULT:
            if set_gpu_power_limit(GPU_POWER_DEFAULT):
                state["gpu_throttled"] = False
                state["current_power_limit"] = GPU_POWER_DEFAULT
                msg = (f"GPU {gpu_util:.0f}% < {GPU_RESTORE}% — "
                       f"restored power limit to {GPU_POWER_DEFAULT}W")
                actions.append(msg)
                _emit(msg, {"gpu_util": gpu_util, "power_limit": GPU_POWER_DEFAULT})

    # ── RAM ──────────────────────────────────────────────────────
    ram_pct = psutil.virtual_memory().percent

    if ram_pct > RAM_CEILING:
        evicted = evict_oldest_model()
        if evicted:
            state["evictions"] = state.get("evictions", 0) + 1
            msg = f"RAM {ram_pct:.0f}% > {RAM_CEILING}% — evicted model: {evicted}"
            actions.append(msg)
            _emit(msg, {"ram_pct": ram_pct, "evicted": evicted})
        else:
            log.info(f"RAM {ram_pct:.0f}% > ceiling but no models to evict")

    state["last_check"] = time.time()
    return actions


# ── Telegram report ───────────────────────────────────────────────────

def format_governor_telegram(actions: list, snap: dict) -> str:
    """Format a Telegram report for governor actions."""
    gpu = snap.get("gpu") or {}
    lines = [
        f"<b>⚙️ RESOURCE GOVERNOR ACTION</b> — {datetime.now():%H:%M}\n",
        f"CPU: <code>{snap['cpu_pct']:.0f}%</code> {'🔴 THROTTLED' if snap['cpu_throttled'] else '🟢 OK'}",
        f"RAM: <code>{snap['ram_pct']:.0f}%</code> ({snap['ram_used_gb']}/{snap['ram_total_gb']} GB)",
    ]
    if gpu:
        lines.append(
            f"GPU: <code>{gpu.get('gpu_util',0):.0f}%</code> util | "
            f"<code>{gpu.get('power_draw',0):.0f}W</code> draw | "
            f"limit <code>{snap['current_power_limit_w']:.0f}W</code> "
            f"{'🔴 THROTTLED' if snap['gpu_throttled'] else '🟢 OK'}"
        )
    lines.append("\n<b>Actions taken:</b>")
    for a in actions:
        lines.append(f"  • {a}")
    return "\n".join(lines)


# ── Main daemon ───────────────────────────────────────────────────────

def main():
    log.info("Resource Governor online.")
    log.info(f"  CPU ceiling: {CPU_CEILING}%  restore: {CPU_RESTORE}%")
    log.info(f"  GPU ceiling: {GPU_CEILING}%  restore: {GPU_RESTORE}%  power: {GPU_POWER_FLOOR}-{GPU_POWER_DEFAULT}W")
    log.info(f"  RAM ceiling: {RAM_CEILING}%  evict on breach")
    log.info(f"  Poll interval: {POLL_INTERVAL}s")

    # Import Telegram sender from sentinel if available
    _send_tg = None
    try:
        from security_sentinel import send_telegram
        _send_tg = send_telegram
        log.info("  Telegram: linked via sentinel")
    except ImportError:
        log.info("  Telegram: not configured (sentinel not importable)")

    state = load_state()
    # Ensure GPU power limit starts at default on launch
    if gpu_stats():
        set_gpu_power_limit(GPU_POWER_DEFAULT)
        state["current_power_limit"] = GPU_POWER_DEFAULT
        state["gpu_throttled"] = False

    _emit("Resource Governor started", {
        "cpu_ceiling": CPU_CEILING, "gpu_ceiling": GPU_CEILING, "ram_ceiling": RAM_CEILING
    })

    while True:
        try:
            actions = run_governor_cycle(state)
            save_state(state)

            if actions:
                log.info(f"Governor actions: {actions}")
                if _send_tg:
                    snap = get_snapshot()
                    msg = format_governor_telegram(actions, snap)
                    _send_tg(msg, "HTML")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log.info("Resource Governor stopping — restoring defaults...")
            renice_pids(_ollama_runner_pids(), nice_val=0)
            if gpu_stats():
                set_gpu_power_limit(GPU_POWER_DEFAULT)
            _emit("Resource Governor stopped")
            break
        except Exception as e:
            log.error(f"Governor cycle error: {e}")
            time.sleep(POLL_INTERVAL)


def print_status():
    """One-shot status report."""
    snap = get_snapshot()
    state = load_state()
    print(f"\n{'='*55}")
    print(f"  RESOURCE GOVERNOR STATUS  —  {snap['timestamp'][:19]}")
    print(f"{'='*55}")
    print(f"  CPU:  {snap['cpu_pct']:5.1f}%  {'[THROTTLED]' if snap['cpu_throttled'] else '[OK]'}")
    print(f"  RAM:  {snap['ram_pct']:5.1f}%  {snap['ram_used_gb']}/{snap['ram_total_gb']} GB")
    gpu = snap.get("gpu")
    if gpu:
        print(f"  GPU:  {gpu['gpu_util']:5.1f}% util  {gpu['power_draw']:.0f}W / {snap['current_power_limit_w']:.0f}W  "
              f"{'[THROTTLED]' if snap['gpu_throttled'] else '[OK]'}")
        print(f"  VRAM: {gpu['vram_used_mb']:5.0f} / {gpu['vram_total_mb']:.0f} MB")
    else:
        print("  GPU:  not available")
    print(f"\n  Thresholds:  CPU<{CPU_CEILING}%  GPU<{GPU_CEILING}%  RAM<{RAM_CEILING}%")
    print(f"  Throttle events: {state.get('throttle_count', 0)}")
    print(f"  Model evictions: {state.get('evictions', 0)}")

    models = ollama_loaded_models()
    if models:
        print(f"\n  Loaded Ollama models ({len(models)}):")
        for m in models:
            vram = m.get("size_vram", 0)
            sz = m.get("size", 0)
            print(f"    • {m['name']}  RAM={sz/1e9:.1f}GB  VRAM={vram/1e6:.0f}MB")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Resource Governor")
    p.add_argument("--status", action="store_true", help="Print one-shot status and exit")
    p.add_argument(
        "--cpu-ceiling", type=int, default=CPU_CEILING,
        help=f"CPU ceiling %% (default {CPU_CEILING})"
    )
    p.add_argument(
        "--gpu-ceiling", type=int, default=GPU_CEILING,
        help=f"GPU ceiling %% (default {GPU_CEILING})"
    )
    p.add_argument(
        "--ram-ceiling", type=int, default=RAM_CEILING,
        help=f"RAM ceiling %% (default {RAM_CEILING})"
    )
    args = p.parse_args()

    CPU_CEILING = args.cpu_ceiling
    GPU_CEILING = args.gpu_ceiling
    RAM_CEILING = args.ram_ceiling

    if args.status:
        print_status()
    else:
        main()
