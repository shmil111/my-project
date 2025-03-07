#!/bin/bash
# Script to update the API status dashboard
# This can be set up as a cron job on Unix systems

echo "Updating API status dashboard..."
cd "$(dirname "$0")"

# Try JavaScript version first
if [ -d "node_modules" ]; then
    echo "Running JavaScript updater..."
    node update_dashboard.js
else
    echo "Node modules not found, checking for Python..."
    
    # Try Python version if Node.js failed
    if command -v python3 &> /dev/null; then
        echo "Running Python updater..."
        python3 update_dashboard.py
    elif command -v python &> /dev/null; then
        echo "Running Python updater..."
        python update_dashboard.py
    else
        echo "ERROR: Neither Node.js nor Python is available"
        exit 1
    fi
fi

echo "API status dashboard updated successfully!" 