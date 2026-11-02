@echo off
title Fuel Bunk Manager - Offline Web App
cd /d "%~dp0"
echo =========================================================
echo   Starting Fuel Bunk Manager - 100%% Offline Web Edition
echo   Zero Internet Required - Local SQLite Database
echo =========================================================
echo.
python main.py --web
pause
