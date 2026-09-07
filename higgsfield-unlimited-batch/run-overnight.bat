@echo off
cd /d "%~dp0"
echo === Higgsfield Unlimited Batch - Overnight Run ===
echo.
echo Keep this window AND the Chrome window open while scenes generate.
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo Node.js is not installed. Get it from https://nodejs.org
  pause
  exit /b 1
)

if not exist node_modules (
  echo Run setup.bat first.
  pause
  exit /b 1
)

if not exist prompts.json (
  echo prompts.json not found. Copy prompts.example.json and edit it.
  pause
  exit /b 1
)

call npm.cmd run batch
echo.
echo Batch finished. Check runs\manifest.jsonl for results.
pause
