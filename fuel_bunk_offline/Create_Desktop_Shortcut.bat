@echo off
title Create Desktop Shortcuts
cd /d "%~dp0"
echo =========================================================
echo   Creating Offline Fuel Bunk Manager Desktop Shortcut...
echo =========================================================
echo.
copy /y "Fuel Bunk Manager - Offline.url" "%USERPROFILE%\Desktop\Fuel Bunk Manager - Offline.url"
echo.
echo =========================================================
echo   SUCCESS: 'Fuel Bunk Manager - Offline' created on Desktop!
echo =========================================================
pause
