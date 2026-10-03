@echo off
echo ==============================================
echo Uploading latest changes to GitHub...
echo ==============================================
cd /d "H:\pettrol pump"

git add .
git commit -m "Auto-update from local folder"
git push -u origin main

echo.
echo ==============================================
echo DONE! Successfully uploaded to GitHub.
echo You can now check your live website.
echo ==============================================
pause
