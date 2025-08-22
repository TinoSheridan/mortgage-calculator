# Simple Dockerfile for test_app.py
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy our simple test app
COPY test_app.py .
COPY debug_start.sh .

# Make debug script executable
RUN chmod +x debug_start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (will be set by Render)
EXPOSE $PORT

# Run the debug script which starts our app
CMD ["./debug_start.sh"]
