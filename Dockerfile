FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production-ready server
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data \
    && chmod -R 755 /app/logs /app/data

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=testing
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
