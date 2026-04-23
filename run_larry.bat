@echo off
REM ============================================================================
REM  run_larry.bat — portable launcher for Agent Larry (Windows 10/11).
REM
REM  Works from any location — local install, USB stick, network share.
REM  Anchors all paths to the directory containing this script via %~dp0; no
REM  hardcoded absolute paths anywhere. If a .venv\ is shipped alongside the
REM  project it is used automatically; otherwise falls back to `py -3` or
REM  `python` on PATH.
REM
REM  Usage:
REM    run_larry.bat                 Launch agent_v2.py interactive CLI
REM    run_larry.bat dashboard       Launch dashboard_hub.py
REM    run_larry.bat paths           Print resolved paths (debug)
REM    run_larry.bat <script.py> ... Run any project script with venv activated
REM ============================================================================
setlocal enableextensions enabledelayedexpansion

REM Resolve project root to this batch file's directory (trailing slash stripped).
set "LARRY_HOME=%~dp0"
if "%LARRY_HOME:~-1%"=="\" set "LARRY_HOME=%LARRY_HOME:~0,-1%"

REM cd into the project so relative paths in scripts behave consistently.
pushd "%LARRY_HOME%" >nul

REM Pick a Python interpreter. Priority:
REM   1. bundled venv   (.venv\Scripts\python.exe) — ships with the project
REM   2. %LARRY_PYTHON% (manual override)
REM   3. py -3          (Python launcher — standard on Win10/11)
REM   4. python         (on PATH)
set "PY="
if exist "%LARRY_HOME%\.venv\Scripts\python.exe" (
    set "PY=%LARRY_HOME%\.venv\Scripts\python.exe"
) else if defined LARRY_PYTHON (
    if exist "%LARRY_PYTHON%" set "PY=%LARRY_PYTHON%"
)
if not defined PY (
    where py >nul 2>&1
    if !errorlevel! == 0 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>&1
    if !errorlevel! == 0 set "PY=python"
)
if not defined PY (
    echo ERROR: no Python interpreter found. Install Python 3.10+ from python.org
    echo or set LARRY_PYTHON to your python.exe path.
    popd >nul
    exit /b 1
)

REM Put project root on PYTHONPATH so relative imports work from any CWD.
if defined PYTHONPATH (
    set "PYTHONPATH=%LARRY_HOME%;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%LARRY_HOME%"
)
if not defined TOKENIZERS_PARALLELISM set "TOKENIZERS_PARALLELISM=false"

REM Dispatch on first argument.
set "CMD=%~1"
if "%CMD%"=="" goto :run_agent
if /I "%CMD%"=="agent"      goto :run_agent
if /I "%CMD%"=="cli"        goto :run_agent
if /I "%CMD%"=="dashboard"  goto :run_dashboard
if /I "%CMD%"=="hub"        goto :run_dashboard
if /I "%CMD%"=="telegram"   goto :run_telegram
if /I "%CMD%"=="paths"      goto :run_paths
if /I "%CMD%"=="where"      goto :run_paths
if /I "%CMD%"=="status"     goto :run_status
if /I "%CMD%"=="help"       goto :show_help
if /I "%CMD%"=="-h"         goto :show_help
if /I "%CMD%"=="--help"     goto :show_help

REM Fallback — run a project script by name.
if exist "%LARRY_HOME%\%CMD%" (
    shift
    %PY% "%LARRY_HOME%\%CMD%" %*
    goto :done
)
%PY% %*
goto :done

:run_agent
shift & set "REST="
:args_agent
if not "%~1"=="" (
    set "REST=!REST! %1"
    shift
    goto :args_agent
)
%PY% "%LARRY_HOME%\agent_v2.py" %REST%
goto :done

:run_dashboard
shift & set "REST="
:args_dash
if not "%~1"=="" (
    set "REST=!REST! %1"
    shift
    goto :args_dash
)
%PY% "%LARRY_HOME%\dashboard_hub.py" %REST%
goto :done

:run_telegram
shift & set "REST="
:args_tg
if not "%~1"=="" (
    set "REST=!REST! %1"
    shift
    goto :args_tg
)
%PY% "%LARRY_HOME%\telegram_bot.py" %REST%
goto :done

:run_paths
%PY% "%LARRY_HOME%\larry_paths.py"
goto :done

:run_status
echo === Agent Larry Status ===
%PY% -c "from larry_paths import __version__; print(f'Version: {__version__}')" 2>nul || echo Version: unknown
echo.
echo --- Python ---
echo Interpreter: %PY%
%PY% --version 2>&1
echo.
echo --- Ollama ---
where ollama >nul 2>&1
if !errorlevel! == 0 (
    ollama --version 2>nul
    echo Models:
    ollama list 2>nul || echo   (not running)
) else (
    echo   Not installed
)
echo.
echo --- GPU ---
where nvidia-smi >nul 2>&1
if !errorlevel! == 0 (
    nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>nul || echo   No NVIDIA GPU
)
echo.
echo --- Docker ---
where docker >nul 2>&1
if !errorlevel! == 0 (
    docker --version 2>nul
    echo Containers:
    docker ps --filter "name=larry-" --format "  {{.Names}}: {{.Status}}" 2>nul || echo   (none running)
) else (
    echo   Not installed
)
echo.
echo --- MCP Servers ---
%PY% -c "from mcp_servers import registry; print(f'Loaded: {len(registry)} - {list(registry.keys())}')" 2>nul || echo   Error loading
goto :done

:show_help
echo.
echo Agent Larry portable launcher (Windows)
echo.
echo Usage: run_larry.bat [command] [args...]
echo.
echo Commands:
echo   agent, cli       Launch agent_v2.py interactive CLI (default)
echo   dashboard, hub   Launch dashboard_hub.py web UI
echo   telegram         Launch telegram_bot.py
echo   status           Show running services, GPU, models, MCP servers
echo   paths, where     Print resolved project paths and exit
echo   ^<script.py^>      Run any project script with venv activated
echo   help             Show this message
echo.
echo Env vars:
echo   LARRY_HOME       Override project root (defaults to script directory)
echo   LARRY_PYTHON     Path to python.exe (overrides auto-detect)
echo   OLLAMA_URL       Ollama API URL (default: http://localhost:11434/api/chat)
echo.

:done
set "RC=%ERRORLEVEL%"
popd >nul
endlocal & exit /b %RC%
