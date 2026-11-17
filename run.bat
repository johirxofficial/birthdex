@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo  BirthDex - Birth ^& Death Verification
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python is not installed or not in PATH.
  echo     Get it from https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [i] Creating a virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [X] Could not create .venv
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [X] Could not activate .venv
  pause
  exit /b 1
)

python -c "import importlib.metadata as m; m.version('birthdex')" >nul 2>nul
if errorlevel 1 (
  echo [i] Installing BirthDex and dependencies ^(first run only^)...
  python -m pip install --upgrade pip >nul
  python -m pip install -e .
  if errorlevel 1 (
    echo [X] pip install failed.
    pause
    exit /b 1
  )
)

if "%PORT%"=="" set PORT=5002
if "%HOST%"=="" set HOST=0.0.0.0
if "%THREADS%"=="" set THREADS=8

echo.
echo   Local:  http://localhost:%PORT%
echo   Health: http://localhost:%PORT%/health
echo   Docs:   docs/API.md
echo.
echo   Press Ctrl+C to stop.
echo.

birthdex --host %HOST% --port %PORT% --threads %THREADS%
pause
