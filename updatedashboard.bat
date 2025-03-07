@echo off
REM Script to update the API status dashboard
REM This can be set up as a scheduled task in Windows

echo Updating API status dashboard...
cd /d %~dp0

REM Try JavaScript version first
if exist "node_modules" (
    echo Running JavaScript updater...
    node update_dashboard.js
) else (
    echo Node modules not found, checking for Python...
    
    REM Try Python version if Node.js failed
    python --version > nul 2>&1
    if %ERRORLEVEL% == 0 (
        echo Running Python updater...
        python update_dashboard.py
    ) else (
        echo ERROR: Neither Node.js nor Python is available
        exit /b 1
    )
)

echo API status dashboard updated successfully! 