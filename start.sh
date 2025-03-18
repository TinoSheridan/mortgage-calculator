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

# Verify gunicorn installation
echo "===== Verifying gunicorn installation ====="
gunicorn_path=$(which gunicorn || echo "NOT_FOUND")
echo "Gunicorn path: $gunicorn_path"
pip list | grep gunicorn

# Show PATH for debugging
echo "===== PATH environment ====="
echo $PATH

# If gunicorn wasn't found in PATH, try a direct module approach
if [ "$gunicorn_path" = "NOT_FOUND" ]; then
    echo "===== Starting with python -m approach ====="
    exec python -m gunicorn app:app --bind 0.0.0.0:$PORT
else
    # Start the application with the found gunicorn
    echo "===== Starting application with gunicorn from PATH ====="
    exec $gunicorn_path app:app --bind 0.0.0.0:$PORT
fi
