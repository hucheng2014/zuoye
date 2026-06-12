import sys

content = """@echo off
echo ============================================
echo   Chrome Debug Launcher (Profile 2 Fix)
echo ============================================
echo.
echo Cleaning up hidden Chrome zombies...
taskkill /F /IM chrome.exe /T >nul 2>&1

set CHROME_USER_DATA=%LOCALAPPDATA%\\Google\\Chrome\\User Data
echo.
echo Launching Chrome on Profile 2...
start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%CHROME_USER_DATA%" --profile-directory="Profile 2" --no-first-run --no-default-browser-check

echo.
echo SUCCESS! Chrome is running on 9222.
pause
"""

with open(r'd:\oneform\start_chrome_debug.bat', 'w', encoding='ascii') as f:
    f.write(content)
