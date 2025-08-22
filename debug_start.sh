#!/bin/bash

echo "=== DEBUG INFO ==="
echo "PWD: $(pwd)"
echo "USER: $(whoami)"
echo "PORT: $PORT"
echo "Python version: $(python3 --version)"
echo "Files in current directory:"
ls -la

echo "=== STARTING APP ==="
python3 test_app.py
