# Simple Dockerfile for Flask app
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our Flask app
COPY ultra_simple_app.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (will be set by Render)
EXPOSE $PORT

# Run the app directly
CMD ["python3", "ultra_simple_app.py"]
