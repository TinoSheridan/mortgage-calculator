#!/usr/bin/env bash
# Combined script for Render deployment
# Handles both installation and startup

# Exit on error
set -o errexit

# Set up path to include common binary locations
export PATH="/opt/render/project/python/venv/bin:/opt/render/project/.venv/bin:/usr/local/bin:$PATH"

# Install dependencies and gunicorn
echo "===== Installing dependencies ====="
pip install -r requirements.txt
pip install gunicorn==21.2.0

# Create necessary directories
echo "===== Creating log directories ====="
mkdir -p logs

# Verify gunicorn installation
echo "===== Verifying gunicorn installation ====="
gunicorn_path=$(which gunicorn || echo "NOT_FOUND")
echo "Gunicorn path: $gunicorn_path"
pip list | grep gunicorn

# Show PATH for debugging
echo "===== PATH environment ====="
echo $PATH

# Start the application with our gunicorn config
echo "===== Starting application with gunicorn config ====="
exec gunicorn app:app -c gunicorn.conf.py --bind 0.0.0.0:$PORT
