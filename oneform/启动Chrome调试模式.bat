@echo off
echo ============================================
echo   Chrome 调试模式启动器
echo ============================================
echo.
echo 请先关闭所有 Chrome 窗口！
echo.
pause

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

echo.
echo Chrome 已关闭
pause
