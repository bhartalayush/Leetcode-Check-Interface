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

:: Register Registry Autostart key based on Database settings to run the launcher directly
python -c "import db, winreg, sys; val = db.get_setting('start_with_windows', 'False'); key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE); winreg.SetValueEx(key, 'DSALock', 0, winreg.REG_SZ, 'cmd.exe /c ' + repr(r'%~dp0run.bat')) if val == 'True' else winreg.DeleteValue(key, 'DSALock') if hasattr(key, 'DeleteValue') else None" 2>nul

:: Start the background daemon with admin privileges
start /b pythonw daemon.py

:: Launch the Streamlit Frontend UI
echo Launching Streamlit Web App Dashboard...
streamlit run app.py --server.headless=true

pause
