#!/usr/bin/env bash
# Combined script for Render deployment
# Handles both installation and startup

# Exit on error
set -o errexit

# Install dependencies and gunicorn
echo "===== Installing dependencies ====="
pip install -r requirements.txt
pip install gunicorn==21.2.0

# Verify gunicorn is available
echo "===== Verifying gunicorn installation ====="
gunicorn_path=$(which gunicorn || echo "NOT_FOUND")
echo "Gunicorn path: $gunicorn_path"
pip list | grep gunicorn

# Start the application
echo "===== Starting application ====="
exec gunicorn app:app --bind 0.0.0.0:$PORT
