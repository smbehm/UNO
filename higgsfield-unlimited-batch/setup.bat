@echo off
cd /d "%~dp0"
echo === Higgsfield Unlimited Batch - Setup ===
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo Node.js is not installed. Get it from https://nodejs.org
  pause
  exit /b 1
)

if not exist node_modules (
  echo Installing dependencies...
  call npm.cmd install
  if errorlevel 1 (
    echo npm install failed.
    pause
    exit /b 1
  )
  echo Installing Playwright browser...
  call npx.cmd playwright install chrome
)

echo.
echo Starting setup - follow the instructions in this window.
call npm.cmd run setup
echo.
pause
