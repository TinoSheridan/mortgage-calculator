# Simple Dockerfile for Flask app
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our simple Flask app
COPY ultra_simple_app.py .
COPY debug_start.sh .

# Make debug script executable
RUN chmod +x debug_start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (will be set by Render)
EXPOSE $PORT

# Run the debug script which starts our app
CMD ["./debug_start.sh"]
