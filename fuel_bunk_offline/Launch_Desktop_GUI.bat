@echo off
title Fuel Bunk Manager - Desktop GUI
cd /d "%~dp0"
echo =========================================================
echo   Starting Fuel Bunk Manager - Native Desktop GUI App
echo   Zero Internet Required - Local SQLite Database
echo =========================================================
echo.
python main.py --gui
pause
