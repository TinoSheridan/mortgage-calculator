# Simple Dockerfile for Flask app
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy our Flask app and calculator dependencies
COPY ultra_simple_app.py .
COPY calculator.py .
COPY constants.py .
COPY config_manager.py .
COPY mortgage_insurance.py .
COPY financed_fees.py .
COPY config/ ./config/
COPY calculations/ ./calculations/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (will be set by Render)
EXPOSE $PORT

# Run the app directly
CMD ["python3", "ultra_simple_app.py"]
