#!/bin/bash
# Fresh start script - completely clean and restart
# This script will forcefully stop all Flask instances, clean cache, and start fresh

echo "===== Stopping all Python web servers ====="
pkill -f "python.*app.py" || true
sleep 2

echo "===== Cleaning all Python cache files ====="
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyc" -delete
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyo" -delete
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyd" -delete

echo "===== Current version in VERSION.py ====="
cat /Users/tinosheridan/Documents/Python/MortgageCalc/VERSION.py

echo "===== Starting application on default port (5000) ====="
cd /Users/tinosheridan/Documents/Python/MortgageCalc
export PYTHONPATH=/Users/tinosheridan/Documents/Python/MortgageCalc
export FLASK_ENV=development
python3 app.py
