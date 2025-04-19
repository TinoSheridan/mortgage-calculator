#!/bin/bash
# Run the application with a specific Python version
# This script finds Python 3.11 and uses it directly

echo "===== Finding Python 3.11 ====="
PYTHON311_PATH=$(ls -1 /usr/local/bin/python3.11 2>/dev/null || ls -1 /usr/bin/python3.11 2>/dev/null || which python3.11 2>/dev/null || echo "")

if [ -z "$PYTHON311_PATH" ]; then
    echo "Python 3.11 not found. Looking for any Python 3.x..."
    PYTHON3_PATH=$(which python3)
    if [ -z "$PYTHON3_PATH" ]; then
        echo "ERROR: No Python 3.x found. Please install Python 3.11."
        exit 1
    fi
    echo "Using $PYTHON3_PATH instead of Python 3.11"
    PYTHON_TO_USE=$PYTHON3_PATH
else
    echo "Found Python 3.11 at: $PYTHON311_PATH"
    PYTHON_TO_USE=$PYTHON311_PATH
fi

echo "===== Stopping any running Python servers ====="
# Force kill all processes using ports 5555, 6789, 7777, 8888, and 9999
lsof -ti:5555,6789,7777,8888,9999 | xargs kill -9 2>/dev/null || true
# Force kill all app.py processes
killall -9 -m python 2>/dev/null || true
killall -9 -m python3 2>/dev/null || true
killall -9 -m python3.11 2>/dev/null || true
pkill -9 -f "python.*app.py" || true
echo "Waiting for processes to terminate..."
sleep 3

echo "===== Removing all Python cache files ====="
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyc" -delete
find /Users/tinosheridan/Documents/Python/MortgageCalc -name "*.pyo" -delete

echo "===== Verifying VERSION.py ====="
cat /Users/tinosheridan/Documents/Python/MortgageCalc/VERSION.py

echo "===== Running application with $PYTHON_TO_USE on port 9999 ====="
cd /Users/tinosheridan/Documents/Python/MortgageCalc
export FLASK_ENV=development
export WTF_CSRF_ENABLED="False"

$PYTHON_TO_USE app.py --port 9999
