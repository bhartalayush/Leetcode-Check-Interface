@echo off
title DSA Lock Launcher

echo ==========================================
echo           Starting DSA Lock System
echo ==========================================

:: Check for Administrative Privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator Privileges...
    powershell -Command "Start-Process '%~dp0run.bat' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

:: Initialize DB
python db.py

:: Create or remove startup shortcut link based on Database settings
python -c "import db, startup_helper; val = db.get_setting('start_with_windows', 'False'); startup_helper.create_startup_shortcut() if val == 'True' else startup_helper.remove_startup_shortcut()" 2>nul

:: Start the background daemon with admin privileges
start /b pythonw daemon.py

:: Launch the Streamlit Frontend UI
echo Launching Streamlit Web App Dashboard...
streamlit run app.py --server.headless=true

pause
