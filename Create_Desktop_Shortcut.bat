@echo off
echo ====================================================
echo Creating Fuel Bunk Manager Desktop Shortcut...
echo ====================================================

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $desktop 'Fuel Bunk Manager.lnk')); $s.TargetPath = 'H:\pettrol pump\FuelBunkManager.exe'; $s.WorkingDirectory = 'H:\pettrol pump'; $s.IconLocation = 'H:\pettrol pump\FuelBunkManager.exe,0'; $s.Save()"

echo.
echo ====================================================
echo SUCCESS: 'Fuel Bunk Manager' shortcut created on Desktop!
echo ====================================================
pause
