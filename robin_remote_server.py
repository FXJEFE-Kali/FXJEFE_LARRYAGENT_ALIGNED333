"""
robin_remote_server.py — Robin remote runner, Windows side.

FastAPI service exposing the same tool surface as agent_tools.py, bound to the
NordVPN Meshnet interface only and bearer-token authenticated.

Deployment is automated by install_on_win11.ps1 (in the same folder).
For manual deployment, see the script's docstring.
"""
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

# ---------- configuration ----------
MESHNET_IP = "100.88.131.215"  # Win11Pro NordVPN Meshnet IP
PORT = 7341

# Allow-list is derived from the current Windows user profile so the same
# file works regardless of the Windows account name. Add or remove paths
# here to change what the agent is allowed to execute remotely.
_USER = Path(os.environ["USERPROFILE"])
WINDOWS_ALLOWED_ROOTS = [
    (_USER / "Documents" / "Agent-Larry").resolve(),
    (_USER / "Documents" / "scripts").resolve(),
    (_USER / "Documents" / "pipelines").resolve(),
    (_USER / "robin").resolve(),  # the install dir, so the server can read its own config
]

STATE_DIR = Path(os.environ["USERPROFILE"]) / ".robin"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "jobs.json"
TOKEN_FILE = STATE_DIR / "token"

if not STATE_FILE.exists():
    STATE_FILE.write_text("{}")

if not TOKEN_FILE.exists():
    raise SystemExit(
        f"Missing token file: {TOKEN_FILE}\n"
        f"Generate one with: python -c \"import secrets; "
        f"open(r'{TOKEN_FILE}', 'w').write(secrets.token_hex(32))\""
    )

TOKEN = TOKEN_FILE.read_text().strip()
if len(TOKEN) < 32:
    raise SystemExit("Token too short. Regenerate with at least 32 hex chars.")


# ---------- security ----------
def _is_relative_to(child: Path, parent: Path) -> bool:
    # Path.is_relative_to is 3.9+; explicit form for cross-version safety.
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _path_allowed(p: str) -> bool:
    try:
        target = Path(p).resolve()
        return any(_is_relative_to(target, root) for root in WINDOWS_ALLOWED_ROOTS)
    except Exception:
        return False


def _check_auth(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    if authorization.removeprefix("Bearer ").strip() != TOKEN:
        raise HTTPException(403, "bad token")


# ---------- state helpers ----------
def _load() -> dict:
    return json.loads(STATE_FILE.read_text())


def _save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------- script runner selection ----------
def _build_command(path: str, args: list[str]) -> list[str]:
    """Pick the right interpreter for .py vs .bat. Reject anything else."""
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return ["python", path, *args]
    if suffix == ".bat":
        return ["cmd.exe", "/c", path, *args]
    raise ValueError(f"unsupported script type: {suffix}")


# ---------- process liveness ----------
def _pid_alive(pid: int) -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5,
        )
        return str(pid) in out.stdout
    except Exception:
        return False


# ---------- tool implementations (mirror Ubuntu side) ----------
def run_script(path: str, args: list[str] | None = None,
               cwd: str | None = None, timeout: int = 120) -> dict:
    if not _path_allowed(path):
        return {"ok": False, "error": "Path is outside the allowed directories"}
    args = args or []
    try:
        cmd = _build_command(path, args)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def start_background(path: str, name: str, args: list[str] | None = None) -> dict:
    if not _path_allowed(path):
        return {"ok": False, "error": "Path is outside the allowed directories"}
    args = args or []
    state = _load()
    existing = state.get(name)
    if isinstance(existing, dict) and "pid" in existing and _pid_alive(existing["pid"]):
        return {"ok": False, "error": f"Job '{name}' is already running (pid {existing['pid']})"}
    try:
        cmd = _build_command(path, args)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    try:
        log_path = STATE_DIR / f"{name}.bg.log"
        log_fh = open(log_path, "ab")
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        creationflags = 0x00000008 | 0x00000200
        proc = subprocess.Popen(
            cmd, stdout=log_fh, stderr=subprocess.STDOUT, creationflags=creationflags,
        )
        state[name] = {
            "pid": proc.pid,
            "path": path,
            "started": time.time(),
            "log": str(log_path),
        }
        _save(state)
        return {"ok": True, "pid": proc.pid, "log": str(log_path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def stop_background(name: str) -> dict:
    state = _load()
    if name not in state or not isinstance(state[name], dict) or "pid" not in state[name]:
        return {"ok": False, "error": f"No background job named '{name}'"}
    pid = state[name]["pid"]
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, check=False,
        )
        del state[name]
        _save(state)
        return {"ok": True, "killed": pid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_jobs() -> dict:
    state = _load()
    out: dict = {}
    for name, info in state.items():
        if isinstance(info, dict) and "pid" in info:
            entry = dict(info)
            entry["alive"] = _pid_alive(info["pid"])
            out[name] = entry
    return {"ok": True, "jobs": out}


def health_check(target: str) -> dict:
    try:
        if target.startswith("http"):
            import urllib.request
            req = urllib.request.Request(target)
            with urllib.request.urlopen(req, timeout=5) as r:
                body = r.read(500).decode("utf-8", errors="replace")
                return {"ok": 200 <= r.status < 400, "status": r.status, "body": body}
        return run_script(target, timeout=30)
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------- FastAPI surface ----------
app = FastAPI(
    title="Robin Remote Runner",
    docs_url=None, redoc_url=None, openapi_url=None,
)


class RunScriptReq(BaseModel):
    path: str
    args: list[str] | None = None
    cwd: str | None = None
    timeout: int = 120


class StartBgReq(BaseModel):
    path: str
    name: str
    args: list[str] | None = None


class NameReq(BaseModel):
    name: str


class HealthReq(BaseModel):
    target: str


@app.get("/ping")
def ping(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return {"ok": True, "host": "win11", "time": time.time()}


@app.post("/run_script")
def api_run_script(req: RunScriptReq, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return run_script(req.path, req.args, req.cwd, req.timeout)


@app.post("/start_background")
def api_start_background(req: StartBgReq, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return start_background(req.path, req.name, req.args)


@app.post("/stop_background")
def api_stop_background(req: NameReq, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return stop_background(req.name)


@app.get("/list_jobs")
def api_list_jobs(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return list_jobs()


@app.post("/health_check")
def api_health_check(req: HealthReq, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return health_check(req.target)


# ---------- entrypoint ----------
if __name__ == "__main__":
    print(f"Robin Remote Runner starting on {MESHNET_IP}:{PORT}")
    print(f"Allow-list: {[str(p) for p in WINDOWS_ALLOWED_ROOTS]}")
    print(f"Token loaded from: {TOKEN_FILE}")
    uvicorn.run(app, host=MESHNET_IP, port=PORT, log_level="info")
