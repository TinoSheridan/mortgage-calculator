#!/bin/bash
# Comprehensive cleanup and restart script
# This script will clean all cache files and restart the application

echo "===== Stopping any running instances ====="
pkill -f "python.*app.py" || true

echo "===== Cleaning all Python cache files ====="
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyc" -delete
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyo" -delete
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyd" -delete

echo "===== Current version in VERSION.py ====="
cat /Users/tinosheridan/Documents/Python/MortgageCalc/VERSION.py | grep "VERSION ="

echo "===== Flushing browser caches ====="
echo "Please clear your browser cache or use incognito mode"

echo "===== Starting application on port 5060 ====="
python /Users/tinosheridan/Documents/Python/MortgageCalc/app.py --port 5060
