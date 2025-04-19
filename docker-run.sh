#!/bin/bash
# Simple Docker build and run script for Mortgage Calculator

echo "===== Building Docker container with Python 3.11 ====="
docker build -t mortgage-calc:1.9.9 .

echo "===== Running container on port 8888 ====="
echo "After the container starts, access the app at: http://localhost:8888"
docker run -p 8888:8000 mortgage-calc:1.9.9
