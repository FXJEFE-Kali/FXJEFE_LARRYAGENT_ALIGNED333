@echo off
REM ============================================================================
REM  verify_docker.bat — Docker deployment verification for Agent Larry (Windows)
REM ============================================================================
REM  Run on Windows 10/11 to confirm Docker + project setup.
REM
REM  Usage:
REM    verify_docker.bat
REM ============================================================================
setlocal enableextensions enabledelayedexpansion

set PASS=0
set FAIL=0
set WARN=0

echo ============================================
echo   Agent Larry — Docker Verification
echo ============================================
echo.

REM ── 1. Docker Engine ──────────────────────────────────────────────────────
echo --- Docker Engine ---
where docker >nul 2>&1
if !errorlevel! == 0 (
    for /f "tokens=*" %%i in ('docker --version 2^>nul') do echo [PASS] Docker installed: %%i
    set /a PASS+=1
) else (
    echo [FAIL] Docker not found. Install Docker Desktop from https://docker.com
    set /a FAIL+=1
    goto :summary
)

docker info >nul 2>&1
if !errorlevel! == 0 (
    echo [PASS] Docker daemon is running
    set /a PASS+=1
) else (
    echo [FAIL] Docker daemon not running. Start Docker Desktop.
    set /a FAIL+=1
    goto :summary
)

REM ── 2. Docker Compose ────────────────────────────────────────────────────
echo.
echo --- Docker Compose ---
docker compose version >nul 2>&1
if !errorlevel! == 0 (
    for /f "tokens=*" %%i in ('docker compose version --short 2^>nul') do echo [PASS] Docker Compose v%%i
    set /a PASS+=1
) else (
    echo [FAIL] Docker Compose not available
    set /a FAIL+=1
)

REM ── 3. Project Files ─────────────────────────────────────────────────────
echo.
echo --- Project Files ---
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%" >nul

for %%f in (Dockerfile docker-compose.yml .env .env.secret.example requirements.txt larry_config.json mcp.json larry_paths.py agent_v2.py) do (
    if exist "%%f" (
        echo [PASS] %%f exists
        set /a PASS+=1
    ) else (
        echo [FAIL] %%f missing
        set /a FAIL+=1
    )
)

if exist ".env.secret" (
    echo [PASS] .env.secret exists
    set /a PASS+=1
) else (
    echo [WARN] .env.secret not found — copy from .env.secret.example
    set /a WARN+=1
)

REM ── 4. Compose Validation ────────────────────────────────────────────────
echo.
echo --- Compose Config ---
docker compose config --quiet >nul 2>&1
if !errorlevel! == 0 (
    echo [PASS] docker-compose.yml is valid
    set /a PASS+=1
) else (
    echo [FAIL] docker-compose.yml has errors
    set /a FAIL+=1
)

REM ── 5. Docker Image ─────────────────────────────────────────────────────
echo.
echo --- Docker Image ---
docker image inspect larry-agent:latest >nul 2>&1
if !errorlevel! == 0 (
    echo [PASS] larry-agent:latest exists
    set /a PASS+=1
) else (
    echo [WARN] larry-agent:latest not built — run: docker build -t larry-agent:latest .
    set /a WARN+=1
)

REM ── 6. GPU ───────────────────────────────────────────────────────────────
echo.
echo --- GPU ---
where nvidia-smi >nul 2>&1
if !errorlevel! == 0 (
    echo [PASS] NVIDIA GPU detected
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>nul
    set /a PASS+=1
) else (
    echo [WARN] No NVIDIA GPU — containers will use CPU only
    set /a WARN+=1
)

REM ── 7. Ollama ────────────────────────────────────────────────────────────
echo.
echo --- Ollama ---
where ollama >nul 2>&1
if !errorlevel! == 0 (
    echo [PASS] Ollama installed
    set /a PASS+=1
    ollama list >nul 2>&1
    if !errorlevel! == 0 (
        echo [PASS] Ollama is running
        set /a PASS+=1
    ) else (
        echo [WARN] Ollama not running — start with: ollama serve
        set /a WARN+=1
    )
) else (
    echo [WARN] Ollama not installed locally — will run in Docker
    set /a WARN+=1
)

REM ── 8. Python ────────────────────────────────────────────────────────────
echo.
echo --- Python ---
set "PY="
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if !errorlevel! == 0 (set "PY=py -3") else (
        where python >nul 2>&1
        if !errorlevel! == 0 set "PY=python"
    )
)
if defined PY (
    for /f "tokens=*" %%i in ('%PY% --version 2^>nul') do echo [PASS] Python: %%i
    set /a PASS+=1
    %PY% -c "from larry_paths import __version__; print(f'[PASS] larry_paths v{__version__}')" 2>nul
    if !errorlevel! == 0 (set /a PASS+=1) else (echo [FAIL] larry_paths import failed & set /a FAIL+=1)
) else (
    echo [WARN] No Python found locally
    set /a WARN+=1
)

:summary
echo.
echo ============================================
echo   Results: %PASS% passed, %FAIL% failed, %WARN% warnings
echo ============================================

if %FAIL% GTR 0 (
    echo Fix the failures above before deploying.
    popd >nul
    endlocal & exit /b 1
) else if %WARN% GTR 0 (
    echo Warnings are non-blocking but should be addressed.
    popd >nul
    endlocal & exit /b 0
) else (
    echo All checks passed! Ready to deploy.
    popd >nul
    endlocal & exit /b 0
)
